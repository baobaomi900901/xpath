#include "widgets_window.h"
#include "range_model.h"
#include <QtWidgets>
#include <algorithm>
#include <random>

namespace {
QPoint mouseGlobalPosition(QMouseEvent *event) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
    return event->globalPosition().toPoint();
#else
    return event->globalPos();
#endif
}
template<class T> T *identify(T *widget, const char *id, const QString &name) {
    widget->setObjectName(QString::fromLatin1(id)); widget->setAccessibleName(name); return widget;
}

// A real QPushButton remains in the accessibility tree; deleting it on hide
// also invalidates cached references held by an automation client.
class DragArena : public QFrame {
public:
    explicit DragArena(DragState *state, QWidget *parent = nullptr) : QFrame(parent), state_(state) {
        setMinimumSize(360, 340); setFrameShape(QFrame::StyledPanel);
        setStyleSheet("DragArena { background: #edf4fc; }");
        setAccessibleName(QStringLiteral("拖拽区域"));
        connect(state_, &DragState::changed, this, [this] { sync(); }); sync();
    }
protected:
    void resizeEvent(QResizeEvent *event) override {
        QFrame::resizeEvent(event); state_->setArea(width(), height());
    }
    bool eventFilter(QObject *watched, QEvent *event) override {
        if (watched != target_) return false;
        if (event->type() == QEvent::MouseButtonPress) {
            auto e = static_cast<QMouseEvent*>(event);
            if (e->button() != Qt::LeftButton) return false;
            state_->begin(e->pos().x(), e->pos().y()); target_->grabMouse(); return true;
        }
        if (event->type() == QEvent::MouseMove) {
            auto e = static_cast<QMouseEvent*>(event);
            auto point = mapFromGlobal(mouseGlobalPosition(e)); state_->move(point.x(), point.y()); return true;
        }
        if (event->type() == QEvent::MouseButtonRelease) {
            auto e = static_cast<QMouseEvent*>(event);
            if (e->button() != Qt::LeftButton) return false;
            auto point = mapFromGlobal(mouseGlobalPosition(e)); state_->move(point.x(), point.y());
            state_->end(); target_->releaseMouse(); return true;
        }
        if (event->type() == QEvent::UngrabMouse) state_->end();
        return false;
    }
private:
    void sync() {
        if (!state_->visible()) { delete target_; target_ = nullptr; return; }
        if (!target_) {
            target_ = identify(new QPushButton("drag-target", this), "drag-target", "drag-target");
            target_->setStyleSheet("background:#2474d2;color:white;border-radius:6px;font-weight:bold;");
            target_->installEventFilter(this); target_->show();
        }
        target_->setGeometry(state_->left(), state_->top(), 120, 80);
    }
    DragState *state_;
    QPushButton *target_ = nullptr;
};
}

RangeWindow::RangeWindow(const QString &mode) {
    setWindowTitle(QStringLiteral("Qt %1 靶场 - Widgets (%2)").arg(qVersion(), mode));
    resize(1100, 820); setMinimumSize(900, 700);
    auto tabs = new QTabWidget(this); setCentralWidget(tabs);
    auto form = identify(new QWidget, "formPage", QStringLiteral("表单控件页"));
    auto scroll = new QScrollArea; scroll->setWidgetResizable(true); scroll->setWidget(form);
    tabs->addTab(scroll, QStringLiteral("表单控件"));
    auto layout = new QVBoxLayout(form); layout->setSpacing(9); layout->setContentsMargins(22,16,22,16);
    auto heading = new QHBoxLayout;
    auto title = new QLabel(QStringLiteral("用户信息表单"));
    title->setStyleSheet("font-size:20px;font-weight:bold"); heading->addWidget(title); heading->addStretch();
    auto popup = identify(new QPushButton(QStringLiteral("展开 Qt 菜单 ▼")), "popupMenu", QStringLiteral("展开 Qt 菜单"));
    heading->addWidget(popup); layout->addLayout(heading);
    auto menuStatus = new QLabel(QStringLiteral("菜单测试: 尚未选择菜单项"));
    identify(menuStatus, "menuStatus", menuStatus->text()); layout->addWidget(menuStatus);
    const QStringList labels{QStringLiteral("姓名"),QStringLiteral("密码"),QStringLiteral("邮箱"),QStringLiteral("年龄"),QStringLiteral("城市（单选）"),QStringLiteral("城市（多选）"),QStringLiteral("性别（单选）"),QStringLiteral("兴趣爱好（多选）"),QStringLiteral("备注"),QStringLiteral("协议")};
    QList<QLineEdit*> edits;
    QList<QCheckBox*> checks;
    QSpinBox *age = nullptr; QComboBox *city = nullptr; QPlainTextEdit *remark = nullptr;
    QRadioButton *male = nullptr;
    std::vector<int> order{0,1,2,3,4,5,6,7,8,9};
    if (mode == "random") { std::mt19937 random(QRandomGenerator::global()->generate()); std::shuffle(order.begin(), order.end(), random); }
    for (int index : order) {
        QWidget *parent = form;
        auto row = new QHBoxLayout; row->setContentsMargins(8,3,8,3);
        if (mode != "flat") {
            auto group = new QFrame(form); group->setObjectName(QString("field%1").arg(index));
            group->setAccessibleName(labels[index]); group->setFrameShape(QFrame::StyledPanel);
            group->setLayout(row); layout->addWidget(group); parent = group;
        } else layout->addLayout(row);
        auto label = new QLabel(labels[index], parent); label->setMinimumWidth(140); row->addWidget(label);
        QWidget *field = nullptr;
        if (index <= 2) {
            const char *ids[] = {"name","password","email"};
            auto edit = identify(new QLineEdit(parent), ids[index], labels[index]);
            if (index == 1) edit->setEchoMode(QLineEdit::Password);
            edits << edit; field = edit;
        } else if (index == 3) {
            age = identify(new QSpinBox(parent), "age", labels[index]); age->setRange(18,80); age->setValue(25); field = age;
        } else if (index == 4) {
            city = identify(new QComboBox(parent), "city", labels[index]);
            city->addItems({QStringLiteral("北京"),QStringLiteral("上海"),QStringLiteral("广州"),QStringLiteral("深圳"),QStringLiteral("杭州")}); field = city;
        } else if (index == 5 || index == 7) {
            const QStringList choices = index == 5 ? QStringList{QStringLiteral("北京"),QStringLiteral("上海"),QStringLiteral("广州"),QStringLiteral("深圳"),QStringLiteral("杭州")} : QStringList{QStringLiteral("阅读"),QStringLiteral("运动"),QStringLiteral("音乐"),QStringLiteral("旅行")};
            for (int j=0; j<choices.size(); ++j) {
                auto check = new QCheckBox(choices[j], parent); check->setObjectName(QString("%1%2").arg(index == 5 ? "cityCheck" : "hobby").arg(j));
                check->setAccessibleName(choices[j]); checks << check; row->addWidget(check);
            }
            row->addStretch();
        } else if (index == 6) {
            auto group = new QButtonGroup(this);
            for (const QString &text : {QStringLiteral("男"),QStringLiteral("女"),QStringLiteral("其他")}) {
                auto radio = new QRadioButton(text, parent); radio->setAccessibleName(text);
                group->addButton(radio); row->addWidget(radio);
                if (!male) { male = radio; male->setChecked(true); }
            }
            row->addStretch();
        } else if (index == 8) {
            remark = identify(new QPlainTextEdit(parent), "remark", labels[index]); remark->setFixedHeight(76); field = remark;
        } else {
            auto check = identify(new QCheckBox(QStringLiteral("同意用户协议"), parent), "agreement", QStringLiteral("同意用户协议")); checks << check; field = check;
        }
        if (field) { label->setBuddy(field); row->addWidget(field, 1); }
    }
    auto actions = new QHBoxLayout;
    auto save = identify(new QPushButton(QStringLiteral("保存")), "save", QStringLiteral("保存"));
    auto reset = identify(new QPushButton(QStringLiteral("重置")), "reset", QStringLiteral("重置"));
    actions->addWidget(save); actions->addWidget(reset); actions->addStretch(); layout->addLayout(actions); layout->addStretch();
    resetForm_ = [=] {
        for (auto edit : edits) edit->clear();
        for (auto check : checks) check->setChecked(false);
        age->setValue(25); city->setCurrentIndex(0); male->setChecked(true); remark->clear();
        for (auto edit : edits) if (edit->accessibleName() == QStringLiteral("姓名")) edit->setFocus();
    };
    connect(reset, &QPushButton::clicked, this, [this] { resetForm_(); });
    connect(save, &QPushButton::clicked, this, [this] { QMessageBox::information(this, QStringLiteral("提示"), QStringLiteral("提交成功")); });
    auto populate = [this, menuStatus](QMenu *menu) {
        auto resetAction = menu->addAction(QStringLiteral("重置表单"));
        connect(resetAction, &QAction::triggered, this, [this,menuStatus] { resetForm_(); menuStatus->setText(QStringLiteral("菜单测试: 重置表单")); });
        auto sub = menu->addMenu(QStringLiteral("更多操作"));
        auto about = sub->addAction(QStringLiteral("关于靶场"));
        connect(about, &QAction::triggered, this, [this,menuStatus] {
            menuStatus->setText(QStringLiteral("菜单测试: 关于靶场"));
            QMessageBox::information(this, QStringLiteral("关于靶场"), QStringLiteral("Qt %1 Widgets RPA 靶场").arg(qVersion()));
        });
    };
    auto file = menuBar()->addMenu(QStringLiteral("文件")); populate(file);
    file->addSeparator(); connect(file->addAction(QStringLiteral("退出")), &QAction::triggered, this, &QWidget::close);
    populate(menuBar()->addMenu(QStringLiteral("编辑")));
    connect(popup, &QPushButton::clicked, this, [=] { QMenu menu(this); populate(&menu); menu.exec(popup->mapToGlobal(QPoint(0,popup->height()))); });
    if (mode == "random") {
        // All form descendants receive fresh IDs once, including grouped items.
        for (auto object : form->findChildren<QWidget*>()) object->setObjectName("random_" + QUuid::createUuid().toString(QUuid::WithoutBraces));
    }

    auto tablePage = new QWidget; tabs->addTab(tablePage, QStringLiteral("表格数据"));
    auto tableLayout = new QVBoxLayout(tablePage); tableLayout->setContentsMargins(20,20,20,20);
    auto model = new EmployeeModel(this);
    auto table = identify(new QTableView, "employeeTable", QStringLiteral("员工数据表格")); table->setModel(model);
    table->setSelectionBehavior(QAbstractItemView::SelectRows); table->setAlternatingRowColors(true);
    table->setEditTriggers(QAbstractItemView::NoEditTriggers); table->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    table->horizontalHeader()->setSectionResizeMode(0, QHeaderView::ResizeToContents);
    tableLayout->addWidget(table);
    auto pageInfo = new QLabel; tableLayout->addWidget(pageInfo);
    auto nav = new QHBoxLayout; tableLayout->addLayout(nav);
    auto navButton = [&](const QString &text, const char *id) { auto b = identify(new QPushButton(text), id, text); nav->addWidget(b); return b; };
    auto first = navButton(QStringLiteral("首页"),"firstPage"), previous = navButton(QStringLiteral("上一页"),"previousPage");
    QList<QPushButton*> pages;
    for (int i=0; i<5; ++i) { auto b = navButton(QString::number(i+1), qPrintable(QString("page%1").arg(i))); pages << b;
        connect(b, &QPushButton::clicked, model, [model,b] { model->setPage(b->text().toInt()); }); }
    auto next = navButton(QStringLiteral("下一页"),"nextPage"), last = navButton(QStringLiteral("末页"),"lastPage"); nav->addStretch();
    connect(first,&QPushButton::clicked,model,[model] { model->setPage(1); });
    connect(previous,&QPushButton::clicked,model,[model] { model->setPage(model->page()-1); });
    connect(next,&QPushButton::clicked,model,[model] { model->setPage(model->page()+1); });
    connect(last,&QPushButton::clicked,model,[model] { model->setPage(50); });
    auto refresh = [=] { pageInfo->setText(model->pageInfo()); first->setEnabled(model->page()>1); previous->setEnabled(model->page()>1);
        next->setEnabled(model->page()<50); last->setEnabled(model->page()<50);
        auto values = model->pageNumbers(); for (int i=0;i<5;++i) { pages[i]->setText(values[i].toString()); pages[i]->setAccessibleName(values[i].toString()); pages[i]->setEnabled(values[i].toInt()!=model->page()); } };
    connect(model,&EmployeeModel::pageChanged,this,refresh); refresh();

    auto dragPage = new QWidget; tabs->addTab(dragPage, QStringLiteral("拖拽测试"));
    auto dragLayout = new QVBoxLayout(dragPage); dragLayout->setContentsMargins(20,20,20,20);
    dragLayout->addWidget(new QLabel(QStringLiteral("拖拽 drag-target，记录位移、锚点、移动次数和耗时；delay_after 由调用方统计。")));
    auto columns = new QHBoxLayout; dragLayout->addLayout(columns,1); auto details = new QVBoxLayout; columns->addLayout(details);
    auto state = new DragState(this); auto summary = new QLabel(state->summary()); summary->setMinimumWidth(330); details->addWidget(summary);
    auto status = new QLabel(state->status()); details->addWidget(status);
    auto resetTarget = identify(new QPushButton(QStringLiteral("重置位置")),"resetTarget",QStringLiteral("重置位置"));
    auto hideTarget = identify(new QPushButton(QStringLiteral("隐藏 drag-target")),"hideTarget",QStringLiteral("隐藏 drag-target"));
    auto copy = identify(new QPushButton(QStringLiteral("复制当前结果")),"copyResult",QStringLiteral("复制当前结果"));
    details->addWidget(resetTarget); details->addWidget(hideTarget); details->addWidget(copy); details->addStretch();
    columns->addWidget(new DragArena(state),1);
    connect(state,&DragState::changed,this,[=] { summary->setText(state->summary()); status->setText(state->status()); hideTarget->setEnabled(state->visible()); });
    connect(resetTarget,&QPushButton::clicked,state,&DragState::reset);
    connect(hideTarget,&QPushButton::clicked,state,&DragState::hide);
    connect(copy,&QPushButton::clicked,state,&DragState::copy);
    statusBar()->showMessage(QStringLiteral("Qt %1 · Widgets · %2").arg(qVersion(),mode));
}
