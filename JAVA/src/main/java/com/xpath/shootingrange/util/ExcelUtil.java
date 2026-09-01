package com.xpath.shootingrange.util;

import com.xpath.shootingrange.model.Employee;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellType;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class ExcelUtil {
    private static final String[] HEADERS = {"ID", "姓名", "部门", "城市", "状态", "邮箱", "入职日期"};

    private ExcelUtil() {
    }

    public static void exportEmployees(Path file, List<Employee> employees) throws IOException {
        try (Workbook workbook = new XSSFWorkbook()) {
            Sheet sheet = workbook.createSheet("员工数据");
            Row headerRow = sheet.createRow(0);
            for (int i = 0; i < HEADERS.length; i++) {
                headerRow.createCell(i).setCellValue(HEADERS[i]);
            }

            for (int rowIndex = 0; rowIndex < employees.size(); rowIndex++) {
                Employee employee = employees.get(rowIndex);
                Row row = sheet.createRow(rowIndex + 1);
                row.createCell(0).setCellValue(employee.id());
                row.createCell(1).setCellValue(employee.name());
                row.createCell(2).setCellValue(employee.department());
                row.createCell(3).setCellValue(employee.city());
                row.createCell(4).setCellValue(employee.status());
                row.createCell(5).setCellValue(employee.email());
                row.createCell(6).setCellValue(employee.joinDate());
            }

            for (int i = 0; i < HEADERS.length; i++) {
                sheet.autoSizeColumn(i);
            }

            try (OutputStream output = Files.newOutputStream(file)) {
                workbook.write(output);
            }
        }
    }

    public static List<Employee> importEmployees(Path file) throws IOException {
        List<Employee> employees = new ArrayList<>();
        try (InputStream input = Files.newInputStream(file);
             Workbook workbook = new XSSFWorkbook(input)) {
            Sheet sheet = workbook.getSheetAt(0);
            int lastRow = sheet.getLastRowNum();
            for (int rowIndex = 1; rowIndex <= lastRow; rowIndex++) {
                Row row = sheet.getRow(rowIndex);
                if (row == null) {
                    continue;
                }
                int id = (int) readNumericCell(row.getCell(0), rowIndex + 1);
                String name = readStringCell(row.getCell(1));
                String department = readStringCell(row.getCell(2));
                String city = readStringCell(row.getCell(3));
                String status = readStringCell(row.getCell(4));
                String email = readStringCell(row.getCell(5));
                String joinDate = readStringCell(row.getCell(6));
                employees.add(new Employee(id, name, department, city, status, email, joinDate));
            }
        }
        return employees;
    }

    private static double readNumericCell(Cell cell, int rowNumber) {
        if (cell == null) {
            throw new IllegalArgumentException("第 " + rowNumber + " 行 ID 不能为空");
        }
        if (cell.getCellType() == CellType.NUMERIC) {
            return cell.getNumericCellValue();
        }
        if (cell.getCellType() == CellType.STRING) {
            return Double.parseDouble(cell.getStringCellValue().trim());
        }
        throw new IllegalArgumentException("第 " + rowNumber + " 行 ID 格式不正确");
    }

    private static String readStringCell(Cell cell) {
        if (cell == null) {
            return "";
        }
        switch (cell.getCellType()) {
            case STRING:
                return cell.getStringCellValue().trim();
            case NUMERIC:
                return String.valueOf((long) cell.getNumericCellValue());
            case BOOLEAN:
                return String.valueOf(cell.getBooleanCellValue());
            default:
                return "";
        }
    }
}
