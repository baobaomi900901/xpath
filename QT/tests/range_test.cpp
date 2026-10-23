#include "range_model.h"
#include "widgets_window.h"
#include <QtTest>
#include <QAccessible>
#include <QCheckBox>
#include <QComboBox>
#include <QLineEdit>
#include <QSpinBox>
#include <QPushButton>
#include <QTabWidget>
#include <QTimer>
#include <QMessageBox>
#include <QClipboard>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickWindow>
#include <QQuickItem>
#include <QMenu>

class RangeTest : public QObject {
    Q_OBJECT
private slots:
    void pagination() {
        EmployeeModel model;
        QCOMPARE(model.rowCount(), 20);
        QCOMPARE(model.columnCount(), 7);
        QCOMPARE(model.data(model.index(0, 0)).toInt(), 1);
        model.setPage(50);
        QCOMPARE(model.data(model.index(19, 0)).toInt(), 1000);
        QCOMPARE(model.pageNumbers(), QVariantList({46,47,48,49,50}));
        model.setPage(999);
        QCOMPARE(model.page(), 50);
        model.setPage(-1);
        QCOMPARE(model.page(), 1);
        QCOMPARE(model.data(model.index(0, 5)).toString(), QString("user1@example.com"));
    }
    void dragBoundsAndReset() {
        DragState drag;
        drag.setArea(600, 400);
        drag.reset();
        QCOMPARE(drag.left(), 240);
        QCOMPARE(drag.top(), 160);
        drag.begin(10, 10);
        drag.move(-100, 900);
        drag.end();
        QCOMPARE(drag.left(), 0);
        QCOMPARE(drag.top(), 320);
        auto json = QJsonDocument::fromJson(drag.json().toUtf8()).object();
        QCOMPARE(json["anchor"].toObject()["sudokuPart"].toString(), QString("topLeft"));
        QCOMPARE(json["sessionDeltaLeft"].toInt(), -240);
        QCOMPARE(json["moveCount"].toInt(), 1);
        QVERIFY(!json["dragging"].toBool());
        drag.hide();
        QVERIFY(!drag.visible());
        drag.reset();
        QVERIFY(drag.visible());
        QCOMPARE(drag.left(), 240);
        QCOMPARE(drag.top(), 160);
    }
    void widgetsFormAndTable() {
        RangeWindow window("grouped");
        window.show();
        QVERIFY(QTest::qWaitForWindowExposed(&window));
        auto name = window.findChild<QLineEdit*>("name");
        QVERIFY(name);
        name->setText(QStringLiteral("测试姓名"));
        window.findChild<QSpinBox*>("age")->setValue(65);
        window.findChild<QCheckBox*>("agreement")->setChecked(true);
        QTest::mouseClick(window.findChild<QPushButton*>("reset"), Qt::LeftButton);
        QCOMPARE(name->text(), QString());
        QCOMPARE(window.findChild<QSpinBox*>("age")->value(), 25);
        QVERIFY(!window.findChild<QCheckBox*>("agreement")->isChecked());
        QCOMPARE(name->parentWidget()->accessibleName(), QStringLiteral("姓名"));
        auto accessible = QAccessible::queryAccessibleInterface(name);
        QVERIFY(accessible);
        QCOMPARE(accessible->text(QAccessible::Name), QStringLiteral("姓名"));
        for (int i=0; i<2; ++i) {
            name->setText("reset via menu");
            QTimer::singleShot(50, [] {
                if (auto menu = qobject_cast<QMenu*>(QApplication::activePopupWidget())) {
                    menu->actions().first()->trigger(); menu->close();
                }
            });
            QTest::mouseClick(window.findChild<QPushButton*>("popupMenu"), Qt::LeftButton);
            QCOMPARE(name->text(), QString());
            QVERIFY(!QApplication::activePopupWidget());
        }
        QTimer::singleShot(30, [] { for (QWidget *w : QApplication::topLevelWidgets())
            if (auto box = qobject_cast<QMessageBox*>(w)) box->accept(); });
        QTest::mouseClick(window.findChild<QPushButton*>("save"), Qt::LeftButton);
        window.findChild<QTabWidget*>()->setCurrentIndex(1);
        QTest::mouseClick(window.findChild<QPushButton*>("lastPage"), Qt::LeftButton);
        QCOMPARE(window.findChild<EmployeeModel*>()->page(), 50);
        QVERIFY(!window.findChild<QPushButton*>("nextPage")->isEnabled());
        window.findChild<QTabWidget*>()->setCurrentIndex(2);
        QCoreApplication::processEvents();
        auto target = window.findChild<QPushButton*>("drag-target");
        auto state = window.findChild<DragState*>();
        QVERIFY(target);
        const int initialLeft = state->left(), initialTop = state->top();
        QCOMPARE(initialLeft, (target->parentWidget()->width() - 120) / 2);
        QCOMPARE(initialTop, (target->parentWidget()->height() - 80) / 2);
        const auto from = target->mapTo(&window, QPoint(12,12));
        const auto to = from + QPoint(50,30);
        QTest::mousePress(window.windowHandle(), Qt::LeftButton, Qt::NoModifier, from);
        QTest::mouseMove(window.windowHandle(), to, 20);
        QTest::mouseRelease(window.windowHandle(), Qt::LeftButton, Qt::NoModifier, to);
        QVERIFY(state->left() > initialLeft);
        QVERIFY(state->top() > initialTop);
        QTest::mouseClick(window.findChild<QPushButton*>("copyResult"), Qt::LeftButton);
        QCOMPARE(QApplication::clipboard()->text(), state->json());
        QTest::mouseClick(window.findChild<QPushButton*>("hideTarget"), Qt::LeftButton);
        QVERIFY(!window.findChild<QPushButton*>("drag-target"));
        QTest::mouseClick(window.findChild<QPushButton*>("resetTarget"), Qt::LeftButton);
        QVERIFY(window.findChild<QPushButton*>("drag-target"));
    }
    void formVariants() {
        RangeWindow flat("flat");
        auto name = flat.findChild<QLineEdit*>("name");
        QCOMPARE(name->parentWidget()->objectName(), QString("formPage"));
        RangeWindow randomA("random"), randomB("random");
        QSet<QString> names;
        for (auto edit : randomA.findChildren<QLineEdit*>()) {
            QVERIFY(!edit->objectName().isEmpty());
            QVERIFY(!names.contains(edit->objectName()));
            names.insert(edit->objectName());
        }
        QVERIFY(randomA.findChildren<QLineEdit*>().first()->objectName() !=
                randomB.findChildren<QLineEdit*>().first()->objectName());
    }
    void quickLoadsAndInteracts() {
        QAccessible::setActive(true);
        EmployeeModel employees;
        DragState drag;
        QQmlApplicationEngine engine;
        QStringList warnings;
        connect(&engine, &QQmlApplicationEngine::warnings, this, [&](const QList<QQmlError> &errors) {
            for (const auto &error : errors) warnings << error.toString();
        });
        engine.rootContext()->setContextProperty("employees", &employees);
        engine.rootContext()->setContextProperty("dragState", &drag);
        engine.rootContext()->setContextProperty("qtVersion", qVersion());
        engine.load(QUrl("qrc:/Range.qml"));
        QVERIFY2(!engine.rootObjects().isEmpty(), qPrintable(warnings.join('\n')));
        auto root = engine.rootObjects().first();
        auto window = qobject_cast<QQuickWindow*>(root);
        QVERIFY(window);
        QVERIFY(QTest::qWaitForWindowExposed(window));
        auto name = root->findChild<QObject*>("name");
        QVERIFY(name);
        name->setProperty("text", QStringLiteral("QML测试"));
        auto resetInterface = QAccessible::queryAccessibleInterface(root->findChild<QObject*>("reset"));
        QVERIFY(resetInterface);
        QVERIFY(resetInterface->actionInterface());
        resetInterface->actionInterface()->doAction(QAccessibleActionInterface::pressAction());
        QTRY_COMPARE(name->property("text").toString(), QString());
        name->setProperty("text", QStringLiteral("QML测试"));
        QVERIFY(QMetaObject::invokeMethod(root, "resetForm"));
        QCOMPARE(name->property("text").toString(), QString());
        QVERIFY(QMetaObject::invokeMethod(root->findChild<QObject*>("save"), "clicked"));
        auto dialog = root->findChild<QObject*>("saveDialog");
        QVERIFY(dialog->property("visible").toBool());
        QVERIFY(QMetaObject::invokeMethod(dialog, "close"));
        for (int i=0; i<2; ++i) {
            QVERIFY(QMetaObject::invokeMethod(root->findChild<QObject*>("popupMenu"), "clicked"));
            auto menu = root->findChild<QObject*>("dynamicPopup");
            QVERIFY(menu);
            QVERIFY(QMetaObject::invokeMethod(menu, "close"));
            QTRY_VERIFY(root->findChild<QObject*>("dynamicPopup") == nullptr);
        }
        QVERIFY(QMetaObject::invokeMethod(root->findChild<QObject*>("lastPage"), "clicked"));
        QCOMPARE(employees.page(), 50);
        root->findChild<QObject*>("tabs")->setProperty("currentIndex", 2);
        QTest::qWait(100);
        auto arena = root->findChild<QQuickItem*>("dragArena");
        auto loader = root->findChild<QQuickItem*>("targetLoader");
        QVERIFY(arena); QVERIFY(loader);
        QCOMPARE(drag.left(), (int(arena->width()) - 120) / 2);
        QCOMPARE(drag.top(), (int(arena->height()) - 80) / 2);
        const int initialLeft = drag.left(), initialTop = drag.top();
        const auto from = loader->mapToScene(QPointF(15,15)).toPoint();
        const auto to = from + QPoint(50,30);
        QTest::mousePress(window, Qt::LeftButton, Qt::NoModifier, from);
        QTest::mouseMove(window, to, 20);
        QTest::mouseRelease(window, Qt::LeftButton, Qt::NoModifier, to);
        QVERIFY(drag.left() > initialLeft);
        QVERIFY(drag.top() > initialTop);
        drag.hide();
        QCoreApplication::processEvents();
        QCOMPARE(root->findChild<QObject*>("targetLoader")->property("active").toBool(), false);
        drag.reset();
        QCoreApplication::processEvents();
        QCOMPARE(root->findChild<QObject*>("targetLoader")->property("active").toBool(), true);
        QVERIFY2(warnings.isEmpty(), qPrintable(warnings.join('\n')));
    }
};
QTEST_MAIN(RangeTest)
#include "range_test.moc"
