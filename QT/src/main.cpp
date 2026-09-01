#include <QDebug>
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlError>
#include <QUrl>

#ifdef Q_OS_WIN
#  include <windows.h>
#endif

static QString g_qmlWarnings;
static bool g_fatalShown = false;

static void showFatal(const QString &message)
{
    if (g_fatalShown)
        return;
    g_fatalShown = true;

    qCritical().noquote() << message;
#ifdef Q_OS_WIN
    MessageBoxW(nullptr,
                reinterpret_cast<LPCWSTR>(message.utf16()),
                L"Acc Hidden Profile",
                MB_OK | MB_ICONERROR);
#endif
}

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);

    QGuiApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("AccHiddenProfile"));
    app.setOrganizationName(QStringLiteral("XPathRange"));
    app.setApplicationDisplayName(QStringLiteral("Acc Hidden Profile"));

    QQmlApplicationEngine engine;
    // Prefer plugins next to the executable (windeployqt output).
    engine.addImportPath(QCoreApplication::applicationDirPath());

    const QUrl url(QStringLiteral("qrc:/main.qml"));

    QObject::connect(
        &engine,
        &QQmlApplicationEngine::warnings,
        &app,
        [](const QList<QQmlError> &warnings) {
            for (const QQmlError &error : warnings) {
                const QString line = error.toString();
                g_qmlWarnings += line + QLatin1Char('\n');
                qWarning().noquote() << line;
            }
        });

    engine.load(url);

    if (engine.rootObjects().isEmpty()) {
        QString details = QStringLiteral("QML load failed.\n");
        if (!g_qmlWarnings.isEmpty())
            details += g_qmlWarnings;
        else
            details += QStringLiteral("No QML warnings captured.\n");
        showFatal(details);
        return -1;
    }

    return app.exec();
}
