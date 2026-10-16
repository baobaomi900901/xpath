$PBExportHeader$pb_range.sra
forward
global type pb_range from application
end type
global transaction sqlca
global dynamicdescriptionarea sqlda
global dynamicstagingarea sqlsa
global error error
global message message
end forward
global type pb_range from application
string appname = "pb_range"
string displayname = "PowerBuilder 靶场"
string appruntimeversion = "25.0.0.3683"
end type
global pb_range pb_range
on pb_range.create
message=create message
sqlca=create transaction
sqlda=create dynamicdescriptionarea
sqlsa=create dynamicstagingarea
error=create error
end on
on pb_range.destroy
destroy(sqlca)
destroy(sqlda)
destroy(sqlsa)
destroy(error)
destroy(message)
end on
event open;
if commandline = "--self-test" then
    f_self_test()
    halt close
else
    open(w_main)
end if
end event
