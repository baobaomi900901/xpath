$PBExportHeader$u_form.sru
forward
global type u_form from userobject
end type
type st_title from statictext within u_form
end type
type cb_menu from commandbutton within u_form
end type
type st_sle_name from statictext within u_form
end type
type sle_name from singlelineedit within u_form
end type
type st_sle_password from statictext within u_form
end type
type sle_password from singlelineedit within u_form
end type
type st_sle_email from statictext within u_form
end type
type sle_email from singlelineedit within u_form
end type
type st_em_age from statictext within u_form
end type
type em_age from editmask within u_form
end type
type st_ddlb_city from statictext within u_form
end type
type ddlb_city from dropdownlistbox within u_form
end type
type st_cities from statictext within u_form
end type
type cb_city1 from checkbox within u_form
end type
type cb_city2 from checkbox within u_form
end type
type cb_city3 from checkbox within u_form
end type
type cb_city4 from checkbox within u_form
end type
type cb_city5 from checkbox within u_form
end type
type st_gender from statictext within u_form
end type
type rb_male from radiobutton within u_form
end type
type rb_female from radiobutton within u_form
end type
type rb_other from radiobutton within u_form
end type
type st_hobbies from statictext within u_form
end type
type cb_hobby1 from checkbox within u_form
end type
type cb_hobby2 from checkbox within u_form
end type
type cb_hobby3 from checkbox within u_form
end type
type cb_hobby4 from checkbox within u_form
end type
type st_remark from statictext within u_form
end type
type mle_remark from multilineedit within u_form
end type
type st_agree from statictext within u_form
end type
type cb_agree from checkbox within u_form
end type
type cb_save from commandbutton within u_form
end type
type cb_reset from commandbutton within u_form
end type
type st_status from statictext within u_form
end type
end forward

global type u_form from userobject
integer width = 4700
integer height = 2650
string text = "表单控件"
string accessiblename = "表单控件"
st_title st_title
cb_menu cb_menu
st_sle_name st_sle_name
sle_name sle_name
st_sle_password st_sle_password
sle_password sle_password
st_sle_email st_sle_email
sle_email sle_email
st_em_age st_em_age
em_age em_age
st_ddlb_city st_ddlb_city
ddlb_city ddlb_city
st_cities st_cities
cb_city1 cb_city1
cb_city2 cb_city2
cb_city3 cb_city3
cb_city4 cb_city4
cb_city5 cb_city5
st_gender st_gender
rb_male rb_male
rb_female rb_female
rb_other rb_other
st_hobbies st_hobbies
cb_hobby1 cb_hobby1
cb_hobby2 cb_hobby2
cb_hobby3 cb_hobby3
cb_hobby4 cb_hobby4
st_remark st_remark
mle_remark mle_remark
st_agree st_agree
cb_agree cb_agree
cb_save cb_save
cb_reset cb_reset
st_status st_status
end type
global u_form u_form

forward prototypes
public subroutine of_reset ()
public subroutine of_save ()
end prototypes

public subroutine of_reset ();
sle_name.Text = ""
sle_password.Text = ""
sle_email.Text = ""
em_age.Text = "25"
if ddlb_city.TotalItems() = 0 then
    ddlb_city.AddItem("北京")
    ddlb_city.AddItem("上海")
    ddlb_city.AddItem("广州")
    ddlb_city.AddItem("深圳")
    ddlb_city.AddItem("杭州")
end if
ddlb_city.SelectItem(1)
rb_male.Checked = true
rb_female.Checked = false
rb_other.Checked = false
mle_remark.Text = ""
cb_agree.Checked = false
cb_city1.Checked = false
cb_city2.Checked = false
cb_city3.Checked = false
cb_city4.Checked = false
cb_city5.Checked = false
cb_hobby1.Checked = false
cb_hobby2.Checked = false
cb_hobby3.Checked = false
cb_hobby4.Checked = false
st_status.Text = "表单已重置"
st_status.AccessibleName = st_status.Text
end subroutine
public subroutine of_save ();
st_status.Text = "表单已提交"
st_status.AccessibleName = st_status.Text
MessageBox("保存", "提交成功", Information!, OK!)
end subroutine

on u_form.create

this.st_title=create st_title
this.cb_menu=create cb_menu
this.st_sle_name=create st_sle_name
this.sle_name=create sle_name
this.st_sle_password=create st_sle_password
this.sle_password=create sle_password
this.st_sle_email=create st_sle_email
this.sle_email=create sle_email
this.st_em_age=create st_em_age
this.em_age=create em_age
this.st_ddlb_city=create st_ddlb_city
this.ddlb_city=create ddlb_city
this.st_cities=create st_cities
this.cb_city1=create cb_city1
this.cb_city2=create cb_city2
this.cb_city3=create cb_city3
this.cb_city4=create cb_city4
this.cb_city5=create cb_city5
this.st_gender=create st_gender
this.rb_male=create rb_male
this.rb_female=create rb_female
this.rb_other=create rb_other
this.st_hobbies=create st_hobbies
this.cb_hobby1=create cb_hobby1
this.cb_hobby2=create cb_hobby2
this.cb_hobby3=create cb_hobby3
this.cb_hobby4=create cb_hobby4
this.st_remark=create st_remark
this.mle_remark=create mle_remark
this.st_agree=create st_agree
this.cb_agree=create cb_agree
this.cb_save=create cb_save
this.cb_reset=create cb_reset
this.st_status=create st_status
this.Control[]={this.st_title,this.cb_menu,this.st_sle_name,this.sle_name,this.st_sle_password,this.sle_password,this.st_sle_email,this.sle_email,this.st_em_age,this.em_age,this.st_ddlb_city,this.ddlb_city,this.st_cities,this.cb_city1,this.cb_city2,this.cb_city3,this.cb_city4,this.cb_city5,this.st_gender,this.rb_male,this.rb_female,this.rb_other,this.st_hobbies,this.cb_hobby1,this.cb_hobby2,this.cb_hobby3,this.cb_hobby4,this.st_remark,this.mle_remark,this.st_agree,this.cb_agree,this.cb_save,this.cb_reset,this.st_status}
end on

on u_form.destroy

destroy(this.st_title)
destroy(this.cb_menu)
destroy(this.st_sle_name)
destroy(this.sle_name)
destroy(this.st_sle_password)
destroy(this.sle_password)
destroy(this.st_sle_email)
destroy(this.sle_email)
destroy(this.st_em_age)
destroy(this.em_age)
destroy(this.st_ddlb_city)
destroy(this.ddlb_city)
destroy(this.st_cities)
destroy(this.cb_city1)
destroy(this.cb_city2)
destroy(this.cb_city3)
destroy(this.cb_city4)
destroy(this.cb_city5)
destroy(this.st_gender)
destroy(this.rb_male)
destroy(this.rb_female)
destroy(this.rb_other)
destroy(this.st_hobbies)
destroy(this.cb_hobby1)
destroy(this.cb_hobby2)
destroy(this.cb_hobby3)
destroy(this.cb_hobby4)
destroy(this.st_remark)
destroy(this.mle_remark)
destroy(this.st_agree)
destroy(this.cb_agree)
destroy(this.cb_save)
destroy(this.cb_reset)
destroy(this.st_status)
end on

type st_title from statictext within u_form
integer x = 120
integer y = 80
integer width = 3000
integer height = 110
integer textsize = -10
string facename = "Microsoft YaHei UI"
string text = "用户信息表单"
string accessiblename = "用户信息表单"
integer weight = 700

end type

type cb_menu from commandbutton within u_form
integer x = 3400
integer y = 60
integer width = 1000
integer height = 140
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "展开原生菜单"
string accessiblename = "展开原生菜单"


end type

event cb_menu.clicked;
m_actions lm_menu
lm_menu = create m_actions
lm_menu.m_popup.PopMenu(w_main.PointerX(), w_main.PointerY())
destroy lm_menu
end event

type st_sle_name from statictext within u_form
integer x = 120
integer y = 266
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "姓名"
string accessiblename = "姓名"


end type

type sle_name from singlelineedit within u_form
integer x = 900
integer y = 250
integer width = 2450
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string accessiblename = "姓名"
integer taborder = 10
boolean border = true
boolean autohscroll = true

end type

type st_sle_password from statictext within u_form
integer x = 120
integer y = 426
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "密码"
string accessiblename = "密码"


end type

type sle_password from singlelineedit within u_form
integer x = 900
integer y = 410
integer width = 2450
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string accessiblename = "密码"
integer taborder = 20
boolean border = true
boolean autohscroll = true
boolean password = true

end type

type st_sle_email from statictext within u_form
integer x = 120
integer y = 586
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "邮箱"
string accessiblename = "邮箱"


end type

type sle_email from singlelineedit within u_form
integer x = 900
integer y = 570
integer width = 2450
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string accessiblename = "邮箱"
integer taborder = 30
boolean border = true
boolean autohscroll = true

end type

type st_em_age from statictext within u_form
integer x = 120
integer y = 746
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "年龄"
string accessiblename = "年龄"


end type

type em_age from editmask within u_form
integer x = 900
integer y = 730
integer width = 800
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string accessiblename = "年龄"
integer taborder = 40
maskdatatype maskdatatype = numericmask!
string mask = "##0"
boolean spin = true
double increment = 1
string minmax = "0~~150"

end type

type st_ddlb_city from statictext within u_form
integer x = 120
integer y = 906
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "城市（单选）"
string accessiblename = "城市（单选）"


end type

type ddlb_city from dropdownlistbox within u_form
integer x = 900
integer y = 890
integer width = 2450
integer height = 700
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string accessiblename = "城市（单选）"
integer taborder = 50
boolean vscrollbar = true
boolean sorted = false

end type

type st_cities from statictext within u_form
integer x = 120
integer y = 1080
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "城市（多选）"
string accessiblename = "城市（多选）"


end type

type cb_city1 from checkbox within u_form
integer x = 900
integer y = 1060
integer width = 470
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "北京"
string accessiblename = "城市（多选）-北京"
integer taborder = 70

end type

type cb_city2 from checkbox within u_form
integer x = 1380
integer y = 1060
integer width = 470
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "上海"
string accessiblename = "城市（多选）-上海"
integer taborder = 80

end type

type cb_city3 from checkbox within u_form
integer x = 1860
integer y = 1060
integer width = 470
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "广州"
string accessiblename = "城市（多选）-广州"
integer taborder = 90

end type

type cb_city4 from checkbox within u_form
integer x = 2340
integer y = 1060
integer width = 470
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "深圳"
string accessiblename = "城市（多选）-深圳"
integer taborder = 100

end type

type cb_city5 from checkbox within u_form
integer x = 2820
integer y = 1060
integer width = 470
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "杭州"
string accessiblename = "城市（多选）-杭州"
integer taborder = 110

end type

type st_gender from statictext within u_form
integer x = 120
integer y = 1250
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "性别（单选）"
string accessiblename = "性别（单选）"


end type

type rb_male from radiobutton within u_form
integer x = 900
integer y = 1230
integer width = 570
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "男"
string accessiblename = "性别（单选）-男"
integer taborder = 120

end type

event rb_male.clicked;
parent.rb_male.Checked = true
parent.rb_female.Checked = false
parent.rb_other.Checked = false
end event

type rb_female from radiobutton within u_form
integer x = 1500
integer y = 1230
integer width = 570
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "女"
string accessiblename = "性别（单选）-女"
integer taborder = 130

end type

event rb_female.clicked;
parent.rb_male.Checked = false
parent.rb_female.Checked = true
parent.rb_other.Checked = false
end event

type rb_other from radiobutton within u_form
integer x = 2100
integer y = 1230
integer width = 570
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "其他"
string accessiblename = "性别（单选）-其他"
integer taborder = 140

end type

event rb_other.clicked;
parent.rb_male.Checked = false
parent.rb_female.Checked = false
parent.rb_other.Checked = true
end event

type st_hobbies from statictext within u_form
integer x = 120
integer y = 1420
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "兴趣爱好（多选）"
string accessiblename = "兴趣爱好（多选）"


end type

type cb_hobby1 from checkbox within u_form
integer x = 900
integer y = 1400
integer width = 570
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "阅读"
string accessiblename = "兴趣爱好（多选）-阅读"
integer taborder = 160

end type

type cb_hobby2 from checkbox within u_form
integer x = 1500
integer y = 1400
integer width = 570
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "运动"
string accessiblename = "兴趣爱好（多选）-运动"
integer taborder = 170

end type

type cb_hobby3 from checkbox within u_form
integer x = 2100
integer y = 1400
integer width = 570
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "音乐"
string accessiblename = "兴趣爱好（多选）-音乐"
integer taborder = 180

end type

type cb_hobby4 from checkbox within u_form
integer x = 2700
integer y = 1400
integer width = 570
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "旅行"
string accessiblename = "兴趣爱好（多选）-旅行"
integer taborder = 190

end type

type st_remark from statictext within u_form
integer x = 120
integer y = 1600
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "备注"
string accessiblename = "备注"


end type

type mle_remark from multilineedit within u_form
integer x = 900
integer y = 1580
integer width = 2450
integer height = 340
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
boolean border = true
boolean vscrollbar = true
integer taborder = 200
string accessiblename = "备注"

end type

type st_agree from statictext within u_form
integer x = 120
integer y = 2010
integer width = 720
integer height = 100
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "协议"
string accessiblename = "协议"


end type

type cb_agree from checkbox within u_form
integer x = 900
integer y = 1990
integer width = 2450
integer height = 130
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "我已阅读并同意用户协议"
string accessiblename = "协议"
integer taborder = 210

end type

type cb_save from commandbutton within u_form
integer x = 900
integer y = 2210
integer width = 650
integer height = 145
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "保存"
string accessiblename = "保存"
integer taborder = 220

end type

event cb_save.clicked;
parent.of_save()
end event

type cb_reset from commandbutton within u_form
integer x = 1680
integer y = 2210
integer width = 650
integer height = 145
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "重置"
string accessiblename = "重置"
integer taborder = 230

end type

event cb_reset.clicked;
parent.of_reset()
end event

type st_status from statictext within u_form
integer x = 120
integer y = 2440
integer width = 4300
integer height = 110
integer textsize = -10
string facename = "Microsoft YaHei UI"
integer weight = 400
string text = "请填写表单，可通过保存和重置测试控件状态。"
string accessiblename = "请填写表单，可通过保存和重置测试控件状态。"


end type
