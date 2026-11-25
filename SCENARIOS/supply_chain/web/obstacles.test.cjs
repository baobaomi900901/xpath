const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function fixture() {
  const node = (attrs={}) => ({attrs:{...attrs},get id(){return this.attrs.id;},set id(v){this.attrs.id=v;},
    getAttribute(k){return this.attrs[k] ?? null;},setAttribute(k,v){this.attrs[k]=v;},hasAttribute(k){return k in this.attrs;}});
  const nodes = [node({id:'plant',name:'plant',list:'plants'}),node({id:'plants'}),node({id:'heading'}),
    node({id:'panel','aria-labelledby':'heading','aria-describedby':'heading extra','aria-controls':'plant plants'}),
    node({for:'plant'}),node({href:'#heading'}),node({href:'/other#heading'})];
  return {nodes,querySelectorAll(selector){return selector==='[id]'?nodes.filter(n=>n.id):nodes;}};
}

function library() {
  const context = {crypto:require('node:crypto').webcrypto};
  vm.createContext(context);
  if (fs.existsSync(__dirname+'/obstacles.js')) vm.runInContext(fs.readFileSync(__dirname+'/obstacles.js','utf8'),context);
  assert.ok(context.InventoryObstacles,'obstacle binding library exists');
  return context.InventoryObstacles;
}

test('normal mode preserves IDs and returns original element references', () => {
  const dom=fixture(), bind=library().bind(dom,false);
  assert.equal(dom.nodes[0].id,'plant');
  assert.equal(bind('plant'),dom.nodes[0]);
});

test('obstacle mode changes all IDs and repairs labels datalists ARIA and local fragments', () => {
  const dom=fixture(), bind=library().bind(dom,true);
  assert.notEqual(dom.nodes[0].id,'plant');
  assert.equal(new Set(dom.nodes.filter(n=>n.id).map(n=>n.id)).size,4);
  assert.equal(bind('plant'),dom.nodes[0]);
  assert.equal(dom.nodes[0].attrs.list,dom.nodes[1].id);
  assert.equal(dom.nodes[3].attrs['aria-labelledby'],dom.nodes[2].id);
  assert.equal(dom.nodes[3].attrs['aria-describedby'],dom.nodes[2].id+' extra');
  assert.equal(dom.nodes[3].attrs['aria-controls'],dom.nodes[0].id+' '+dom.nodes[1].id);
  assert.equal(dom.nodes[4].attrs.for,dom.nodes[0].id);
  assert.equal(dom.nodes[5].attrs.href,'#'+dom.nodes[2].id);
  assert.equal(dom.nodes[6].attrs.href,'/other#heading');
});

test('new page loads generate different IDs while business names remain stable', () => {
  const lib=library(), first=fixture(), second=fixture();
  lib.bind(first,true);lib.bind(second,true);
  assert.notEqual(first.nodes[0].id,second.nodes[0].id);
  assert.equal(first.nodes[0].attrs.name,'plant');
  assert.equal(second.nodes[0].attrs.name,'plant');
});
