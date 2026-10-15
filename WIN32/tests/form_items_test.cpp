// Exercise the model and MSAA provider in-process, without creating an app window.
#include "../src/msaa_main.cpp"

#include <iostream>
#include <stdexcept>

namespace {

void Require(bool condition, const char* message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
VARIANT Self() {
    VARIANT child{};
    child.vt = VT_I4;
    child.lVal = CHILDID_SELF;
    return child;
}

std::wstring Name(IAccessible* accessible, VARIANT child) {
    BSTR name{};
    Require(accessible->get_accName(child, &name) == S_OK, "Name must resolve");
    const std::wstring result(name, SysStringLen(name));
    SysFreeString(name);
    return result;
}

IAccessible* Pane(IAccessible* root, const wchar_t* name) {
    long count{};
    Require(root->get_accChildCount(&count) == S_OK, "Root children must enumerate");
    for (long index = 1; index <= count; ++index) {
        VARIANT child = Self();
        child.lVal = index;
        VARIANT role{};
        Require(root->get_accRole(child, &role) == S_OK, "Child role must resolve");
        if (role.lVal != ROLE_SYSTEM_PANE || Name(root, child) != name) {
            continue;
        }
        IDispatch* dispatch{};
        Require(root->get_accChild(child, &dispatch) == S_OK && dispatch, "Pane must be an accessible object");
        IAccessible* accessible{};
        const HRESULT result = dispatch->QueryInterface(IID_IAccessible, reinterpret_cast<void**>(&accessible));
        dispatch->Release();
        Require(result == S_OK, "Pane must expose IAccessible");
        return accessible;
    }
    throw std::runtime_error("Missing named form Pane");
}

void VerifyPane(IAccessible* root, const wchar_t* name, const std::vector<std::wstring>& names) {
    IAccessible* pane = Pane(root, name);
    long count{};
    Require(pane->get_accChildCount(&count) == S_OK && count == static_cast<long>(names.size()),
            "Pane must contain only its own label and controls");
    std::vector<VARIANT> children(count);
    long obtained{};
    Require(AccessibleChildren(pane, 0, count, children.data(), &obtained) == S_OK && obtained == count,
            "AccessibleChildren must enumerate the Pane");
    for (long index = 0; index < count; ++index) {
        std::wstring childName;
        if (children[index].vt == VT_DISPATCH) {
            IAccessible* accessible{};
            Require(children[index].pdispVal->QueryInterface(IID_IAccessible, reinterpret_cast<void**>(&accessible)) == S_OK,
                    "Enumerated child must expose IAccessible");
            childName = Name(accessible, Self());
            accessible->Release();
        } else {
            Require(children[index].vt == VT_I4, "Enumerated child must be an object or child ID");
            childName = Name(pane, children[index]);
        }
        Require(childName == names[index], "Pane child names must stay within their form field");
        VariantClear(&children[index]);
    }
    IDispatch* parent{};
    Require(pane->get_accParent(&parent) == S_OK && parent, "Pane must have its root parent");
    IAccessible* parentAccessible{};
    Require(parent->QueryInterface(IID_IAccessible, reinterpret_cast<void**>(&parentAccessible)) == S_OK,
            "Parent must expose IAccessible");
    Require(Name(parentAccessible, Self()) == kWindowTitle, "Pane parent must be the root");
    parentAccessible->Release();
    parent->Release();
    pane->Release();
}

IAccessible* Object(VARIANT& value) {
    Require(value.vt == VT_DISPATCH && value.pdispVal, "Navigation must return an accessible object");
    IAccessible* result{};
    Require(value.pdispVal->QueryInterface(IID_IAccessible, reinterpret_cast<void**>(&result)) == S_OK,
            "Navigation object must expose IAccessible");
    VariantClear(&value);
    return result;
}

void VerifyNavigation(IAccessible* root) {
    IAccessible* city = Pane(root, L"城市（多选）");
    IAccessible* hobbies = Pane(root, L"兴趣爱好（多选）");
    VARIANT cityChild = Self();
    cityChild.lVal = 2;
    IDispatch* childDispatch{};
    Require(city->get_accChild(cityChild, &childDispatch) == S_OK && childDispatch,
            "Tree enumeration must expose the same checkbox object used by focus and events");
    IAccessible* canonicalCheckbox{};
    Require(childDispatch->QueryInterface(IID_IAccessible, reinterpret_cast<void**>(&canonicalCheckbox)) == S_OK,
            "Checkbox must expose IAccessible");
    childDispatch->Release();
    g_app.focusedKey = CityMultiFirst;
    VARIANT focus{};
    Require(root->get_accFocus(&focus) == S_OK, "Root must resolve focus through a field Pane");
    IAccessible* focused = Object(focus);
    Require(Name(focused, Self()) == L"北京", "Root focus must resolve the city checkbox");
    Require(focused == canonicalCheckbox, "Root focus and tree traversal must identify the same checkbox");
    focused->Release();
    Require(city->get_accFocus(&focus) == S_OK, "City Pane must resolve its focused child");
    focused = Object(focus);
    Require(Name(focused, Self()) == L"北京", "City focus must resolve its checkbox");
    focused->Release();
    Require(hobbies->get_accFocus(&focus) == S_FALSE && focus.vt == VT_EMPTY,
            "Hobby Pane must not resolve focus from the city Pane");

    VARIANT last = Self();
    last.lVal = 6;
    VARIANT next{};
    Require(city->accNavigate(NAVDIR_NEXT, last, &next) == S_FALSE,
            "City checkbox sibling navigation must stop at the city Pane boundary");
    Require(city->accNavigate(NAVDIR_NEXT, Self(), &next) == S_OK,
            "Field Pane sibling navigation must resolve the next field");
    IAccessible* nextPane = Object(next);
    Require(Name(nextPane, Self()) == L"性别（单选）", "The next field must be gender");
    nextPane->Release();

    VARIANT hit{};
    Require(city->accHitTest(182, 277, &hit) == S_OK, "City Pane hit test must find its checkbox");
    IAccessible* hitObject = Object(hit);
    Require(Name(hitObject, Self()) == L"北京", "Hit test must stay inside the city Pane");
    hitObject->Release();
    Require(hobbies->accHitTest(182, 277, &hit) == S_FALSE,
            "Hobby Pane hit test must not return city controls");
    city->Release();
    hobbies->Release();
    canonicalCheckbox->Release();
}

void VerifyIdentity(IAccessible* root) {
    IAccessible* first = Pane(root, L"城市（多选）");
    IAccessible* second = Pane(root, L"城市（多选）");
    Require(first == second, "Repeated requests for the same Pane must keep its COM identity");
    first->Release();
    second->Release();
}

void VerifyDropdown(IAccessible* root) {
    IAccessible* city = Pane(root, L"城市（单选）");
    long rootCount{};
    long childCount{};
    Require(root->get_accChildCount(&rootCount) == S_OK, "Root children must enumerate");
    Require(city->get_accChildCount(&childCount) == S_OK && childCount == 2,
            "Collapsed city Pane must contain its label and combo box");
    g_app.cityComboExpanded = true;
    VerifyPane(root, L"城市（单选）", {L"城市（单选）", L"城市（单选）", L"北京", L"上海", L"广州", L"深圳", L"杭州"});
    long expandedRootCount{};
    Require(root->get_accChildCount(&expandedRootCount) == S_OK && expandedRootCount == rootCount,
            "Dropdown options must change the city Pane's children without changing root children");
    g_app.cityComboExpanded = false;
    Require(city->get_accChildCount(&childCount) == S_OK && childCount == 2,
            "Collapsed city Pane must remove its dropdown options");
    city->Release();
}
#endif

} // namespace

int main() {
    try {
        const auto elements = BuildElements(nullptr);
        const auto paneCount = std::count_if(elements.begin(), elements.end(), [](const Element& element) {
            return element.role == ROLE_SYSTEM_PANE;
        });
        Require(paneCount == 10, "Each of the ten form fields must have a Pane");
        for (const Element& element : elements) {
            const bool fieldLabel = element.key >= FormLabelFirst && element.key < FormLabelFirst + 10;
            const bool fieldControl = element.role == ROLE_SYSTEM_CHECKBUTTON || element.role == ROLE_SYSTEM_RADIOBUTTON
                || element.role == ROLE_SYSTEM_TEXT || element.role == ROLE_SYSTEM_COMBOBOX
                || element.role == ROLE_SYSTEM_SPINBUTTON;
            if (fieldLabel || fieldControl) {
                const Element* parent = FindElementByKey(elements, element.parentKey);
                Require(parent && parent->role == ROLE_SYSTEM_PANE, "Every field label and control must belong to a Pane");
            }
        }
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
        Require(SUCCEEDED(OleInitialize(nullptr)), "OLE initialization must succeed");
        auto* root = new MsaaAccessible(nullptr);
        g_app.accessible = root;
        VerifyPane(root, L"城市（多选）", {L"城市（多选）", L"北京", L"上海", L"广州", L"深圳", L"杭州"});
        VerifyPane(root, L"兴趣爱好（多选）", {L"兴趣爱好（多选）", L"阅读", L"运动", L"音乐", L"旅行"});
        VerifyPane(root, L"性别（单选）", {L"性别（单选）", L"男", L"女", L"其他"});
        VerifyPane(root, L"协议", {L"协议", L"同意用户协议"});
        VerifyNavigation(root);
        VerifyIdentity(root);
        VerifyDropdown(root);
        root->Release();
        g_app.accessible = nullptr;
        OleUninitialize();
#endif
        std::cout << "Form Pane checks passed without launching an application.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
