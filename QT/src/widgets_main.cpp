#include "widgets_window.h"
#include <QApplication>
#include <QCommandLineParser>
#include <QTimer>
#include <QScreen>
#include <QTabWidget>

int main(int argc, char **argv) {
#if QT_VERSION < QT_VERSION_CHECK(6, 0, 0)
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
#endif
    QApplication app(argc, argv);
    app.setFont(QFont(QStringLiteral("Microsoft YaHei UI"), 10));
    QCommandLineParser parser; parser.addHelpOption();
    parser.addOption({"form-mode", "grouped, flat or random", "mode", "grouped"});
    parser.addOption({"smoke-test", "Open the real window briefly and exit"});
    parser.addOption({"screenshot", "Save a screenshot before smoke-test exit", "file"});
    parser.addOption({"page", "Initial page: 0=form, 1=table, 2=drag", "index", "0"});
    parser.process(app);
    const auto mode = parser.value("form-mode");
    if (mode != "grouped" && mode != "flat" && mode != "random") return 2;
    RangeWindow window(mode); window.show();
    bool pageValid = false;
    const int page = parser.value("page").toInt(&pageValid);
    if (!pageValid || page < 0 || page > 2) return 2;
    window.findChild<QTabWidget*>()->setCurrentIndex(page);
    if (parser.isSet("smoke-test")) QTimer::singleShot(800, &app, [&] {
        bool ok = true;
        if (parser.isSet("screenshot")) ok = window.grab().save(parser.value("screenshot"));
        app.exit(ok ? 0 : 3);
    });
    return app.exec();
}
