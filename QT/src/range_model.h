#pragma once
#include <QAbstractTableModel>
#include <QElapsedTimer>
#include <QVariantList>

class EmployeeModel : public QAbstractTableModel {
    Q_OBJECT
    Q_PROPERTY(int page READ page WRITE setPage NOTIFY pageChanged)
    Q_PROPERTY(QString pageInfo READ pageInfo NOTIFY pageChanged)
    Q_PROPERTY(QVariantList pageNumbers READ pageNumbers NOTIFY pageChanged)
    Q_PROPERTY(QVariantList rows READ rows NOTIFY pageChanged)
public:
    explicit EmployeeModel(QObject *parent = nullptr) : QAbstractTableModel(parent) {}
    int rowCount(const QModelIndex &parent = {}) const override { return parent.isValid() ? 0 : 20; }
    int columnCount(const QModelIndex &parent = {}) const override { return parent.isValid() ? 0 : 7; }
    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
    QVariant headerData(int section, Qt::Orientation orientation, int role) const override;
    int page() const { return page_; }
    Q_INVOKABLE void setPage(int page);
    QString pageInfo() const;
    QVariantList pageNumbers() const;
    QVariantList rows() const;
signals:
    void pageChanged();
private:
    int page_ = 1;
};

class DragState : public QObject {
    Q_OBJECT
    Q_PROPERTY(int left READ left NOTIFY changed)
    Q_PROPERTY(int top READ top NOTIFY changed)
    Q_PROPERTY(bool visible READ visible NOTIFY changed)
    Q_PROPERTY(QString summary READ summary NOTIFY changed)
    Q_PROPERTY(QString status READ status NOTIFY changed)
public:
    explicit DragState(QObject *parent = nullptr) : QObject(parent) {}
    int left() const { return left_; }
    int top() const { return top_; }
    bool visible() const { return visible_; }
    QString status() const { return status_; }
    QString summary() const;
    Q_INVOKABLE QString json() const;
    Q_INVOKABLE void setArea(int width, int height);
    Q_INVOKABLE void reset();
    Q_INVOKABLE void hide();
    Q_INVOKABLE void begin(int x, int y);
    Q_INVOKABLE void move(int areaX, int areaY);
    Q_INVOKABLE void end();
    Q_INVOKABLE void copy();
signals:
    void changed();
private:
    int width_ = 600, height_ = 400;
    int left_ = 240, top_ = 160, initialLeft_ = 240, initialTop_ = 160;
    int startLeft_ = 240, startTop_ = 160, anchorX_ = 60, anchorY_ = 40, moves_ = 0;
    qint64 duration_ = 0;
    bool dragging_ = false, visible_ = true, initialized_ = false;
    QString region_ = "middleCenter", status_ = QStringLiteral("状态: 空闲");
    QElapsedTimer timer_;
};
