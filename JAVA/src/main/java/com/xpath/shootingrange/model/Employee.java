package com.xpath.shootingrange.model;

import java.util.Objects;

public final class Employee {
    private final int id;
    private final String name;
    private final String department;
    private final String city;
    private final String status;
    private final String email;
    private final String joinDate;

    public Employee(int id, String name, String department, String city, String status, String email,
                    String joinDate) {
        this.id = id;
        this.name = name;
        this.department = department;
        this.city = city;
        this.status = status;
        this.email = email;
        this.joinDate = joinDate;
    }

    public int id() {
        return id;
    }

    public String name() {
        return name;
    }

    public String department() {
        return department;
    }

    public String city() {
        return city;
    }

    public String status() {
        return status;
    }

    public String email() {
        return email;
    }

    public String joinDate() {
        return joinDate;
    }

    @Override
    public boolean equals(Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof Employee)) {
            return false;
        }
        Employee employee = (Employee) other;
        return id == employee.id
                && Objects.equals(name, employee.name)
                && Objects.equals(department, employee.department)
                && Objects.equals(city, employee.city)
                && Objects.equals(status, employee.status)
                && Objects.equals(email, employee.email)
                && Objects.equals(joinDate, employee.joinDate);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name, department, city, status, email, joinDate);
    }

    @Override
    public String toString() {
        return "Employee[id=" + id
                + ", name=" + name
                + ", department=" + department
                + ", city=" + city
                + ", status=" + status
                + ", email=" + email
                + ", joinDate=" + joinDate + "]";
    }
}
