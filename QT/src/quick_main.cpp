#include "range_model.h"
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickWindow>
#include <QTimer>
#include <QCommandLineParser>

int main(int argc, char **argv) {
#if QT_VERSION < QT_VERSION_CHECK(6, 0, 0)
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
#endif
    QGuiApplication app(argc, argv);
    QCommandLineParser parser; parser.addHelpOption();
    parser.addOption({"smoke-test", "Open the real window briefly and exit"});
    parser.addOption({"screenshot", "Save a screenshot before smoke-test exit", "file"});
    parser.addOption({"page", "Initial page: 0=form, 1=table, 2=drag", "index", "0"});
    parser.process(app);
    EmployeeModel employees;
    DragState drag;
    QQmlApplicationEngine engine;
    bool warnings = false;
    QObject::connect(&engine, &QQmlApplicationEngine::warnings, &app, [&](const QList<QQmlError>&) { warnings = true; });
    engine.rootContext()->setContextProperty("employees", &employees);
    engine.rootContext()->setContextProperty("dragState", &drag);
    engine.rootContext()->setContextProperty("qtVersion", qVersion());
    engine.load(QUrl("qrc:/Range.qml"));
    if (engine.rootObjects().isEmpty()) return 1;
    bool pageValid = false;
    const int page = parser.value("page").toInt(&pageValid);
    if (!pageValid || page < 0 || page > 2) return 2;
    engine.rootObjects().first()->findChild<QObject*>("tabs")->setProperty("currentIndex", page);
    if (parser.isSet("smoke-test")) QTimer::singleShot(1000, &app, [&] {
        bool ok = !warnings;
        if (parser.isSet("screenshot")) {
            auto window = qobject_cast<QQuickWindow*>(engine.rootObjects().first());
            ok = window && window->grabWindow().save(parser.value("screenshot")) && ok;
        }
        app.exit(ok ? 0 : 3);
    });
    return app.exec();
}
