#pragma once
#include <QMainWindow>
#include <functional>

class RangeWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit RangeWindow(const QString &formMode = "grouped");
private:
    std::function<void()> resetForm_;
};
