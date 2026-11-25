#pragma once
#include <algorithm>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
// Guards native control construction and rejects duplicate or stale timer work.
class WorkspaceLoad {
  enum class State { Waiting, Loading, Ready, Cancelled };
  State state;
public:
  explicit WorkspaceLoad(bool obstacles = false)
      : state(obstacles ? State::Waiting : State::Ready) {}
  bool ready() const { return state == State::Ready; }
  bool loading() const { return state == State::Loading; }
  bool begin() {
    if (state != State::Waiting) return false;
    state = State::Loading;
    return true;
  }
  bool complete() {
    if (!loading()) return false;
    state = State::Ready;
    return true;
  }
  void cancel() { state = State::Cancelled; }
};
struct Table {
  std::vector<std::string> headers;
  std::vector<std::vector<std::string>> rows;
  size_t column(const std::string &name) const {
    auto i = std::find(headers.begin(), headers.end(), name);
    if (i == headers.end())
      throw std::runtime_error("Missing column: " + name);
    return i - headers.begin();
  }
};
inline Table parseTsv(std::string text) {
  if (text.compare(0, 3, "\xEF\xBB\xBF") == 0)
    text.erase(0, 3);
  Table t;
  std::istringstream in(text);
  std::string line;
  bool first = true;
  while (std::getline(in, line)) {
    if (!line.empty() && line.back() == '\r')
      line.pop_back();
    if (line.empty())
      continue;
    std::vector<std::string> row;
    size_t pos = 0, next;
    do {
      next = line.find('\t', pos);
      row.push_back(
          line.substr(pos, next == std::string::npos ? next : next - pos));
      pos = next + 1;
    } while (next != std::string::npos);
    if (first) {
      t.headers = row;
      first = false;
    } else {
      if (row.size() != t.headers.size())
        throw std::runtime_error("Malformed TSV row");
      t.rows.push_back(row);
    }
  }
  if (first)
    throw std::runtime_error("Empty TSV response");
  return t;
}
inline long long priceCents(const std::string &v) {
  auto p = v.find('.');
  if (p == std::string::npos || v.size() - p != 3 || p == 0)
    throw std::runtime_error("Invalid price");
  long long n = 0;
  for (char c : v) {
    if (c == '.')
      continue;
    if (c < '0' || c > '9' || n > 100000000000LL)
      throw std::runtime_error("Invalid price");
    n = n * 10 + c - '0';
  }
  return n;
}
inline std::string urlEncode(const std::string &s) {
  std::string out;
  const char *hex = "0123456789ABCDEF";
  for (unsigned char c : s) {
    if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
        (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.')
      out += c;
    else {
      out += '%';
      out += hex[c >> 4];
      out += hex[c & 15];
    }
  }
  return out;
}
#include <filesystem>
#include <fstream>
inline void saveBinaryFile(const std::filesystem::path &path,
                           const std::string &bytes) {
  std::ofstream file(path, std::ios::binary | std::ios::trunc);
  if (!file)
    throw std::runtime_error("无法打开目标文件");
  file.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
  file.flush();
  if (!file)
    throw std::runtime_error("写入或刷新文件失败");
  file.close();
  if (file.fail())
    throw std::runtime_error("关闭文件失败");
}
