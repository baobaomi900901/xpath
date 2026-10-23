#include "range_model.h"
#include <QGuiApplication>
#include <QClipboard>
#include <QStringList>
#include <algorithm>

QVariant EmployeeModel::data(const QModelIndex &index, int role) const {
    if (!index.isValid() || index.row() >= 20 || index.column() >= 7 || role != Qt::DisplayRole) return {};
    const int id = (page_ - 1) * 20 + index.row() + 1;
    const QStringList departments{QStringLiteral("研发部"),QStringLiteral("产品部"),QStringLiteral("市场部"),QStringLiteral("销售部"),QStringLiteral("人事部")};
    const QStringList cities{QStringLiteral("北京"),QStringLiteral("上海"),QStringLiteral("广州"),QStringLiteral("深圳"),QStringLiteral("杭州")};
    const QStringList statuses{QStringLiteral("在职"),QStringLiteral("离职"),QStringLiteral("待入职")};
    switch (index.column()) {
    case 0: return id;
    case 1: return QStringLiteral("用户%1").arg(id);
    case 2: return departments[id % 5];
    case 3: return cities[id % 5];
    case 4: return statuses[id % 3];
    case 5: return QString("user%1@example.com").arg(id);
    default: return QString("2024-%1-%2").arg(id % 12 + 1, 2, 10, QLatin1Char('0')).arg(id % 28 + 1, 2, 10, QLatin1Char('0'));
    }
}
QVariant EmployeeModel::headerData(int section, Qt::Orientation orientation, int role) const {
    if (role != Qt::DisplayRole) return {};
    if (orientation == Qt::Vertical) return section + 1;
    const QStringList labels{QStringLiteral("ID"),QStringLiteral("姓名"),QStringLiteral("部门"),QStringLiteral("城市"),QStringLiteral("状态"),QStringLiteral("邮箱"),QStringLiteral("入职日期")};
    return section >= 0 && section < labels.size() ? QVariant(labels[section]) : QVariant();
}
void EmployeeModel::setPage(int page) {
    page = std::clamp(page, 1, 50);
    if (page == page_) return;
    beginResetModel(); page_ = page; endResetModel(); emit pageChanged();
}
QString EmployeeModel::pageInfo() const {
    return QStringLiteral("第 %1 / 50 页，当前显示 %2 - %3 条（共 1000 条）").arg(page_).arg((page_-1)*20+1).arg(page_*20);
}
QVariantList EmployeeModel::pageNumbers() const {
    QVariantList result;
    int start = std::clamp(page_ - 2, 1, 46);
    for (int i = 0; i < 5; ++i) result << start + i;
    return result;
}
QVariantList EmployeeModel::rows() const {
    QVariantList result;
    for (int row = 0; row < 20; ++row) {
        QVariantList cells;
        for (int col = 0; col < 7; ++col) cells << data(index(row, col));
        result << QVariant(cells);
    }
    return result;
}
void DragState::setArea(int width, int height) {
    width_ = std::max(120, width); height_ = std::max(80, height);
    if (!initialized_) { reset(); return; }
    left_ = std::clamp(left_, 0, width_ - 120); top_ = std::clamp(top_, 0, height_ - 80);
    emit changed();
}
void DragState::reset() {
    initialized_ = true; visible_ = true; dragging_ = false;
    left_ = initialLeft_ = startLeft_ = (width_ - 120) / 2;
    top_ = initialTop_ = startTop_ = (height_ - 80) / 2;
    anchorX_ = 60; anchorY_ = 40; region_ = "middleCenter";
    moves_ = 0; duration_ = 0; status_ = QStringLiteral("状态: 空闲"); emit changed();
}
void DragState::hide() { end(); visible_ = false; status_ = QStringLiteral("元素已隐藏"); emit changed(); }
void DragState::begin(int x, int y) {
    if (!visible_) return;
    anchorX_ = std::clamp(x, 0, 119); anchorY_ = std::clamp(y, 0, 79);
    static const char *regions[] = {"topLeft","topCenter","topRight","middleLeft","middleCenter","middleRight","bottomLeft","bottomCenter","bottomRight"};
    region_ = regions[(anchorY_ * 3 / 80) * 3 + anchorX_ * 3 / 120];
    startLeft_ = left_; startTop_ = top_; moves_ = 0; duration_ = 0;
    dragging_ = true; timer_.start(); status_ = QStringLiteral("状态: 拖拽中"); emit changed();
}
void DragState::move(int areaX, int areaY) {
    if (!dragging_) return;
    int x = std::clamp(areaX - anchorX_, 0, width_ - 120), y = std::clamp(areaY - anchorY_, 0, height_ - 80);
    if (x == left_ && y == top_) return;
    left_ = x; top_ = y; ++moves_; emit changed();
}
void DragState::end() {
    if (!dragging_) return;
    dragging_ = false; duration_ = timer_.elapsed(); status_ = QStringLiteral("状态: 空闲"); emit changed();
}
QString DragState::json() const {
    // Explicit order matches the Win32 clipboard contract.
    return QString("{\"left\":%1,\"top\":%2,\"initialLeft\":%3,\"initialTop\":%4,\"deltaLeft\":%5,\"deltaTop\":%6,\"startLeft\":%7,\"startTop\":%8,\"sessionDeltaLeft\":%9,\"sessionDeltaTop\":%10,\"anchor\":{\"x\":%11,\"y\":%12,\"sudokuPart\":\"%13\"},\"moveCount\":%14,\"durationMs\":%15,\"dragging\":%16}")
        .arg(left_).arg(top_).arg(initialLeft_).arg(initialTop_).arg(left_-initialLeft_).arg(top_-initialTop_)
        .arg(startLeft_).arg(startTop_).arg(left_-startLeft_).arg(top_-startTop_)
        .arg(anchorX_).arg(anchorY_).arg(region_).arg(moves_).arg(duration_).arg(dragging_ ? "true" : "false");
}
QString DragState::summary() const {
    return QStringLiteral("当前位置: left=%1, top=%2\n相对初始位移: Δleft=%3, Δtop=%4\n\n按下锚点: x=%5, y=%6\nsudoku_part=%7\n\n本次位移: Δleft=%8, Δtop=%9\nmove=%10, duration=%11ms")
        .arg(left_).arg(top_).arg(left_-initialLeft_).arg(top_-initialTop_).arg(anchorX_).arg(anchorY_).arg(region_)
        .arg(left_-startLeft_).arg(top_-startTop_).arg(moves_).arg(duration_);
}
void DragState::copy() {
    const auto text = json(); QGuiApplication::clipboard()->setText(text);
    status_ = QGuiApplication::clipboard()->text() == text ? QStringLiteral("已复制当前结果") : QStringLiteral("复制失败");
    emit changed();
}
