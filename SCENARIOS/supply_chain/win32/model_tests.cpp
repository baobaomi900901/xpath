#undef NDEBUG
#include "model.h"
#include <cassert>
#include <fstream>
#include <iostream>
int main() {
  WorkspaceLoad eager(false);
  assert(eager.ready() && !eager.begin() && !eager.complete());
  WorkspaceLoad lazy(true);
  assert(!lazy.ready() && !lazy.loading() && !lazy.complete());
  assert(lazy.begin() && lazy.loading() && !lazy.ready());
  assert(!lazy.begin());
  assert(lazy.complete() && lazy.ready() && !lazy.loading());
  assert(!lazy.complete() && !lazy.begin());
  WorkspaceLoad cancelled(true);
  assert(cancelled.begin());
  cancelled.cancel();
  assert(!cancelled.loading() && !cancelled.ready());
  assert(!cancelled.complete() && !cancelled.begin());
  auto t =
      parseTsv("\xEF\xBB\xBFmaterial_id\tname\r\nM001\t螺丝\r\nM002\t\r\n");
  assert(t.headers.size() == 2 && t.rows.size() == 2 && t.rows[1][1].empty());
  assert(t.column("name") == 1);
  bool missing = false;
  try {
    t.column("missing");
  } catch (...) {
    missing = true;
  }
  assert(missing);
  bool bad = false;
  try {
    parseTsv("a\tb\nonly\n");
  } catch (...) {
    bad = true;
  }
  assert(bad);
  assert(priceCents("10.05") == 1005 &&
         priceCents("9.00") < priceCents("10.00"));
  bad = false;
  try {
    priceCents("1.x");
  } catch (...) {
    bad = true;
  }
  assert(bad);
  std::vector<std::string> prices = {"10.00", "9.00", "10.05"};
  std::stable_sort(prices.begin(), prices.end(), [](auto &a, auto &b) {
    return priceCents(a) < priceCents(b);
  });
  assert(prices[0] == "9.00" && prices[2] == "10.05");
  assert(urlEncode("M001,M003") == "M001%2CM003");
  const std::string binary("PK\0\xff\r\n", 6);
  saveBinaryFile("supplier-save-test.xlsx", binary);
  std::ifstream saved("supplier-save-test.xlsx", std::ios::binary);
  std::string actual((std::istreambuf_iterator<char>(saved)), {});
  assert(actual == binary);
  saved.close();
  std::remove("supplier-save-test.xlsx");
  bool writeFailed = false;
  try {
    saveBinaryFile("missing-test-dir/file.xlsx", binary);
  } catch (...) {
    writeFailed = true;
  }
  assert(writeFailed);
  std::cout << "model tests passed\n";
}
