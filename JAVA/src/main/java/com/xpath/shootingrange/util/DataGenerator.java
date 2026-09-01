package com.xpath.shootingrange.util;

import com.xpath.shootingrange.model.Employee;

import java.util.ArrayList;
import java.util.List;

public final class DataGenerator {
    private static final String[] DEPARTMENTS = {"研发部", "产品部", "市场部", "销售部", "人事部"};
    private static final String[] CITIES = {"北京", "上海", "广州", "深圳", "杭州"};
    private static final String[] STATUSES = {"在职", "离职", "待入职"};

    private DataGenerator() {
    }

    public static List<Employee> buildEmployees(int total) {
        List<Employee> rows = new ArrayList<>(total);
        for (int index = 0; index < total; index++) {
            int id = index + 1;
            rows.add(new Employee(
                    id,
                    "用户" + id,
                    DEPARTMENTS[id % DEPARTMENTS.length],
                    CITIES[id % CITIES.length],
                    STATUSES[id % STATUSES.length],
                    "user" + id + "@example.com",
                    String.format("2024-%02d-%02d", (id % 12) + 1, (id % 28) + 1)
            ));
        }
        return rows;
    }
}
