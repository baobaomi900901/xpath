"""Small real OOXML workbooks, using inline strings; accepts Excel shared strings too."""
import io
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

INVENTORY_COLUMNS = ["batch_id", "material_id", "name", "unit", "plant", "warehouse", "current", "safety", "target", "enabled"]
QUOTE_COLUMNS = ["quote_id", "material_id", "supplier_id", "supplier_name", "unit_price", "available", "moq", "lead_days", "valid_until", "active", "currency", "unit"]
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def column_name(index):
    result = ""
    while index:
        index, digit = divmod(index - 1, 26)
        result = chr(65 + digit) + result
    return result


def write_xlsx(sheets):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        content = ['<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
                   '<Default Extension="xml" ContentType="application/xml"/>',
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>']
        workbook, relationships = [], []
        for sheet_number, (name, columns, rows) in enumerate(sheets, 1):
            content.append(f'<Override PartName="/xl/worksheets/sheet{sheet_number}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
            workbook.append(f'<sheet name="{escape(name, {chr(34): "&quot;"})}" sheetId="{sheet_number}" r:id="rId{sheet_number}"/>')
            relationships.append(f'<Relationship Id="rId{sheet_number}" Type="{REL}/worksheet" Target="worksheets/sheet{sheet_number}.xml"/>')
            xml = [f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{NS}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" state="frozen"/></sheetView></sheetViews><cols>']
            for index in range(1, len(columns) + 1):
                xml.append(f'<col min="{index}" max="{index}" width="22" customWidth="1"/>')
            xml.append('</cols><sheetData>')
            all_rows = [columns] + [[row.get(key, "") for key in columns] for row in rows]
            for row_number, values in enumerate(all_rows, 1):
                xml.append(f'<row r="{row_number}">')
                for col, value in enumerate(values, 1):
                    ref = f"{column_name(col)}{row_number}"
                    if isinstance(value, bool):
                        xml.append(f'<c r="{ref}" t="b"><v>{int(value)}</v></c>')
                    elif isinstance(value, (int, float)):
                        xml.append(f'<c r="{ref}"><v>{value}</v></c>')
                    else:
                        xml.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(str(value))}</t></is></c>')
                xml.append('</row>')
            xml.append('</sheetData></worksheet>')
            z.writestr(f"xl/worksheets/sheet{sheet_number}.xml", "".join(xml))
        z.writestr("[Content_Types].xml", "".join(content) + "</Types>")
        z.writestr("_rels/.rels", f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="{REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{NS}" xmlns:r="{REL}"><sheets>{"".join(workbook)}</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(relationships) + '</Relationships>')
    return output.getvalue()


def read_xlsx(data):
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("文件超过 8MB")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if len(z.infolist()) > 128 or sum(i.file_size for i in z.infolist()) > 32 * 1024 * 1024:
                raise ValueError("工作簿过大")
            if "[Content_Types].xml" not in z.namelist():
                raise ValueError("不是有效的 xlsx")
            strings = []
            if "xl/sharedStrings.xml" in z.namelist():
                strings = ["".join(n.itertext()) for n in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(f"{{{NS}}}si")]
            relationships = {n.attrib["Id"]: n.attrib["Target"] for n in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
            result = {}
            for sheet in ET.fromstring(z.read("xl/workbook.xml")).findall(f"{{{NS}}}sheets/{{{NS}}}sheet"):
                target = relationships[sheet.attrib[f"{{{REL}}}id"]]
                filename = posixpath.normpath("xl/" + target) if not target.startswith("/") else target.lstrip("/")
                rows = []
                for row in ET.fromstring(z.read(filename)).findall(f"{{{NS}}}sheetData/{{{NS}}}row"):
                    values = []
                    for cell in row:
                        if cell.find(f"{{{NS}}}f") is not None:
                            raise ValueError("导入库存不能包含公式")
                        letters = re.match(r"[A-Z]+", cell.attrib.get("r", "A1"))[0]
                        index = 0
                        for char in letters:
                            index = index * 26 + ord(char) - 64
                        if index > 256:
                            raise ValueError("列数过多")
                        while len(values) < index:
                            values.append("")
                        kind = cell.attrib.get("t")
                        raw = cell.findtext(f"{{{NS}}}v", "")
                        if kind == "inlineStr":
                            inline = cell.find(f"{{{NS}}}is")
                            if inline is None:
                                raise ValueError("工作簿包含不完整的文本单元格")
                            raw = "".join(inline.itertext())
                        elif kind == "s":
                            raw = strings[int(raw)]
                        elif kind == "b":
                            raw = "true" if raw == "1" else "false"
                        values[index - 1] = raw
                    rows.append(values)
                result[sheet.attrib["name"]] = rows
            return result
    except (zipfile.BadZipFile, KeyError, ET.ParseError, IndexError, TypeError) as error:
        raise ValueError("无法读取 xlsx 工作簿") from error
