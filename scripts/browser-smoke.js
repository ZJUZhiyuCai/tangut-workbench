// Run through Playwright CLI's run-code --filename after opening the built site.
// This is an interactive browser smoke check, not a source of linguistic verification.
async (page) => {
  const checks = [];
  const assert = (condition, name) => {
    if (!condition) throw new Error(name);
    checks.push(name);
  };
  const search = page.getByRole('searchbox', {name: '检索字形、编码、字书编号或释义'});
  const filter = page.getByRole('combobox', {name: '范围'});
  await page.getByRole('button', {name:'字词检索', exact:true}).click();
  await filter.selectOption('all');
  for (const query of ['𗞈', 'U+17788', 'L4267', '葡萄', 'grape']) {
    await search.fill(query);
    assert((await page.locator('#result-count').innerText()) === '1 个字头', `lookup ${query}`);
    await page.getByRole('button', {name:'查看 U+17788 葡萄', exact:true}).click();
    assert((await page.locator('#detail').innerText()).includes('p.513, entry 4267'), `source locator ${query}`);
  }
  await search.fill('');
  await filter.selectOption('checked');
  assert(await page.locator('.result').count() === 2, 'checked filter');
  await filter.selectOption('lexical');
  assert(await page.locator('.result').count() === 5, 'lexical filter');
  await filter.selectOption('all');
  assert(await page.locator('.result').count() === 40, 'first result page');
  await page.getByRole('button', {name:'再显示 40 个字头'}).click();
  assert(await page.locator('.result').count() === 80, 'pagination');
  await search.fill('U+18D1E');
  await page.getByRole('button', {name:'查看 U+18D1E 暂无词义记录'}).click();
  assert((await page.locator('#detail').innerText()).includes('随附字体暂未覆盖此字'), 'font gap fallback');
  assert((await page.locator('#detail').innerText()).includes('尚未整理词义'), 'no invented gloss');
  await search.fill('<script>alert(1)</script>');
  assert((await page.locator('#results').innerText()).includes('没有匹配'), 'literal input and empty result');
  await search.fill('');
  await page.getByRole('button', {name:'查看 U+17788 葡萄', exact:true}).click();
  await page.getByRole('link', {name:/^H3 \/ /}).click();
  await page.locator('#inv5875-H3[open]').waitFor({state:'visible'});
  assert(await page.locator('#inv5875-H3').getAttribute('open') !== null, 'hypothesis deep link');
  assert((await page.locator('.research-counts').innerText()).includes('0 段新增完整译文'), 'honest translation count');
  assert(await page.locator('.gap-table tbody tr').count() === 4, 'four unread regions');
  await page.getByRole('button', {name:'参与积累', exact:true}).click();
  assert((await page.getByRole('link', {name:'提交证据', exact:true}).getAttribute('href')).includes('template=evidence.yml'), 'contribution entry');
  await page.getByRole('button', {name:'字词检索', exact:true}).click();
  await search.focus();
  await page.keyboard.press('Tab');
  assert(await page.getByRole('button', {name:'清空检索'}).evaluate(el=>el===document.activeElement), 'keyboard focus order');
  await filter.selectOption('lexical');
  await page.setViewportSize({width:1360,height:1000});
  await page.evaluate(()=>document.fonts.ready);
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'output/playwright/desktop.png',fullPage:true,animations:'disabled'});
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('button', {name:'查看 U+177A4 苗', exact:true}).click();
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth), 'mobile has no horizontal overflow');
  assert(await page.locator('#detail').evaluate(el=>el.getBoundingClientRect().top<innerHeight), 'mobile selection reveals detail');
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'output/playwright/mobile.png',fullPage:true,animations:'disabled'});
  await page.emulateMedia({reducedMotion:'reduce'});
  assert(await page.locator('.detail-inner').evaluate(el=>getComputedStyle(el).animationName==='none'), 'reduced motion');
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.setViewportSize({width:1360,height:1000});
  return {passed:checks.length,checks};
}
