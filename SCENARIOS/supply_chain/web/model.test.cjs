const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = {URLSearchParams};
vm.createContext(context);
const source = fs.existsSync(__dirname + '/model.js') ? fs.readFileSync(__dirname + '/model.js', 'utf8') : '';
vm.runInContext(source, context);
test('pagination uses eight rows, clamps bounds, and handles empty results', () => {
  assert.ok(context.InventoryModel, 'inventory model exists');
  const rows = Array.from({length: 19}, (_, i) => ({current:i}));
  assert.equal(context.InventoryModel.view(rows, 'current', 'asc', 2).rows[0].current, 8);
  assert.equal(context.InventoryModel.view(rows, 'current', 'asc', 99).rows.length, 3);
  assert.equal(context.InventoryModel.view([], 'current', 'asc', 0).page, 1);
});
test('sorting compares numbers numerically and leaves source data unchanged', () => {
  assert.ok(context.InventoryModel, 'inventory model exists');
  const rows = [{current:2},{current:100},{current:10}];
  assert.equal(context.InventoryModel.view(rows, 'current', 'desc', 1).rows[0].current,100);
  assert.equal(rows[0].current,2);
});
test('export encodes full applied query without page parameters', () => {
  assert.ok(context.InventoryModel, 'inventory model exists');
  const query = context.InventoryModel.query({plant:' 华东工厂 ',warehouse:'一号仓',search:'A&B'});
  assert.equal(new URLSearchParams(query).get('search'),'A&B');
  assert.equal(new URLSearchParams(query).get('plant'),'华东工厂');
  assert.equal(new URLSearchParams(query).has('page'),false);
});
test('reset submits cleared filters immediately rather than the previous query', () => {
  const elements = new Map(), requests = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {value:'',listeners:{},setAttribute(){},addEventListener(event, fn){this.listeners[event]=fn;}});
    return elements.get(id);
  };
  const browser = {URLSearchParams, InventoryModel:context.InventoryModel, InventoryObstacles:{bind:()=>element},
    document:{documentElement:{dataset:{}},getElementById:element,querySelectorAll:()=>[]},
    fetch:url=>{requests.push(url);return new Promise(()=>{});}};
  vm.createContext(browser);
  vm.runInContext(fs.readFileSync(__dirname + '/app.js','utf8'),browser);
  element('plant').value='华东工厂'; element('warehouse').value='一号仓'; element('search').value='M019';
  let prevented = false;
  element('filters').listeners.reset({preventDefault(){prevented=true;}});
  assert.equal(prevented,true);
  assert.equal(requests.at(-1),'/api/inventory?');
  assert.equal(element('search').value,'');
});
