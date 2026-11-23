/* 札幌湯匠 — 購物車、結帳與頁面動態（無外部套件） */
(() => {
  'use strict';
  const D = JSON.parse(document.getElementById('ys-data').textContent);
  const T = D.t;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = (n) => 'NT$' + Number(n).toLocaleString('en-US');
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const P = Object.fromEntries(D.products.map((p) => [p.id, p]));
  const root = document.documentElement;

  /* ───────── 購物車（瀏覽器本機儲存） ───────── */
  const KEY = 'ys_cart_v1';
  let mem = [];
  function read() {
    let c;
    try { c = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { c = mem; }
    if (!Array.isArray(c)) return [];
    return c.filter((i) => P[i.id] && i.qty > 0).map((i) => ({ id: i.id, qty: Math.min(Math.floor(i.qty), P[i.id].max) }));
  }
  function write(c) {
    mem = c;
    try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) { /* 私密模式：只存在記憶體 */ }
    badge(true);
    document.dispatchEvent(new Event('cart:change'));
  }
  const count = () => read().reduce((a, i) => a + i.qty, 0);
  function badge(pop) {
    const n = count();
    $$('[data-cart-count]').forEach((b) => {
      b.textContent = n > 99 ? '99+' : n;
      b.hidden = n === 0;
      if (pop && !reduce) { b.classList.remove('pop'); void b.offsetWidth; b.classList.add('pop'); }
    });
  }
  function add(id, qty) {
    const c = read();
    const f = c.find((i) => i.id === id);
    if (f) f.qty = Math.min(f.qty + qty, P[id].max); else c.push({ id, qty: Math.min(qty, P[id].max) });
    write(c);
  }
  function setQty(id, qty) {
    let c = read();
    if (qty <= 0) c = c.filter((i) => i.id !== id);
    else { const f = c.find((i) => i.id === id); if (f) f.qty = Math.min(qty, P[id].max); }
    write(c);
  }
  const shipFor = (sub) => (D.ship.fee == null ? null : D.ship.free != null && sub >= D.ship.free ? 0 : D.ship.fee);
  const totals = (c) => {
    const sub = c.reduce((a, i) => a + P[i.id].price * i.qty, 0);
    const sh = shipFor(sub);
    return { sub, sh, total: sub + (sh || 0) };
  };
  badge(false);

  /* ───────── 提示訊息 ───────── */
  let toastTimer;
  function toast(html) {
    const t = $('.toast');
    if (!t) return;
    t.innerHTML = html;
    t.hidden = false;
    requestAnimationFrame(() => t.classList.add('on'));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.classList.remove('on'); setTimeout(() => { t.hidden = true; }, 400); }, 3400);
  }

  /* 商品圖飛進購物車 */
  function fly(img) {
    if (reduce || !img) return;
    const target = $$('.hd__cart, .mbar__cart').find((el) => el.getClientRects().length && getComputedStyle(el).display !== 'none');
    if (!target) return;
    const a = img.getBoundingClientRect();
    const b = target.getBoundingClientRect();
    const c = img.cloneNode();
    c.removeAttribute('loading');
    c.className = 'fly';
    Object.assign(c.style, { left: a.left + 'px', top: a.top + 'px', width: a.width + 'px', height: a.height + 'px' });
    document.body.appendChild(c);
    const dx = b.left + b.width / 2 - (a.left + a.width / 2);
    const dy = b.top + b.height / 2 - (a.top + a.height / 2);
    const anim = c.animate(
      [{ transform: 'translate(0,0) scale(1)', opacity: 1 }, { transform: `translate(${dx * 0.5}px,${dy - 120}px) scale(.45)`, opacity: 0.9, offset: 0.55 }, { transform: `translate(${dx}px,${dy}px) scale(.06)`, opacity: 0.3 }],
      { duration: 820, easing: 'cubic-bezier(.45,0,.2,1)' }
    );
    anim.onfinish = () => { c.remove(); target.classList.remove('bump'); void target.offsetWidth; target.classList.add('bump'); };
  }

  /* 數量加減 */
  document.addEventListener('click', (e) => {
    const s = e.target.closest('[data-step]');
    if (!s) return;
    const inp = s.parentElement.querySelector('input');
    const min = inp.min === '' ? 1 : +inp.min;
    const max = +inp.max || 99;
    inp.value = Math.max(min, Math.min(max, (parseInt(inp.value, 10) || 0) + +s.dataset.step));
    inp.dispatchEvent(new Event('change', { bubbles: true }));
  });

  /* 加入購物車 */
  document.addEventListener('submit', (e) => {
    const f = e.target.closest('.atc');
    if (!f) return;
    e.preventDefault();
    const id = f.dataset.id;
    const q = Math.max(1, Math.min(P[id].max, parseInt(f.elements.qty.value, 10) || 1));
    add(id, q);
    let img = (f.closest('.ptile, .pd') || document).querySelector('img');
    const dlg = f.closest('dialog');
    if (dlg) { img = dlg._from || null; dlg.close(); }
    fly(img);
    const b = f.querySelector('.atc__btn');
    b.classList.add('done');
    setTimeout(() => b.classList.remove('done'), 1500);
    toast(`<span>${esc(T.added.replace('{n}', P[id].name + ' × ' + q))}</span><a href="${D.cartUrl}">${esc(T.toCart)} ›</a>`);
  });

  /* ───────── 購物車頁 ───────── */
  function summaryHTML(c, withButton) {
    const { sub, sh, total } = totals(c);
    let prog = '';
    if (D.ship.free != null) {
      const left = Math.max(0, D.ship.free - sub);
      prog = `<div class="freebar"><p>${sh === 0 ? esc(T.free) + ' ✓' : esc(T.freeLeft.replace('{n}', fmt(left)))}</p><span style="--p:${Math.min(100, (sub / D.ship.free) * 100).toFixed(1)}%"></span></div>`;
    }
    return `${prog}<dl class="sum__dl"><div><dt>${esc(T.subtotal)}</dt><dd>${fmt(sub)}</dd></div>`
      + `<div><dt>${esc(T.shipping)}</dt><dd>${sh == null ? esc(T.shipTbd) : sh === 0 ? esc(T.free) : fmt(sh)}</dd></div>`
      + `<div class="sum__total"><dt>${esc(T.total)}</dt><dd>${fmt(total)}</dd></div></dl>`
      + (withButton ? `<a class="buy" href="${D.checkoutUrl}"><b>${esc(T.checkout)}</b><i aria-hidden="true">›</i></a>` : '');
  }
  function renderCart() {
    const el = $('#cart-root');
    if (!el) return;
    const c = read();
    if (!c.length) {
      el.innerHTML = `<div class="cart__empty"><p>${esc(T.empty)}</p><a class="btn btn--navy" href="${D.shopUrl}"><span>${esc(T.toShop)}</span><i aria-hidden="true">›</i></a></div>`;
      return;
    }
    const rows = c.map((i) => {
      const p = P[i.id];
      return `<li class="ci" data-id="${p.id}"><a class="ci__img" href="${p.url}"><img src="${p.img}" alt=""></a>`
        + `<div class="ci__info"><a class="ci__name" href="${p.url}">${esc(p.name)}</a><p class="ci__meta">${esc(p.net)}　${fmt(p.price)}</p>`
        + `<button type="button" class="ci__rm" data-rm="${p.id}">${esc(T.remove)}</button></div>`
        + `<div class="qty"><button type="button" data-step="-1" aria-label="−">−</button><input type="number" min="0" max="${p.max}" value="${i.qty}" data-ci="${p.id}" aria-label="${esc(T.qty)}"><button type="button" data-step="1" aria-label="+">+</button></div>`
        + `<p class="ci__line">${fmt(p.price * i.qty)}</p></li>`;
    }).join('');
    el.innerHTML = `<ul class="ci__list">${rows}</ul><aside class="sum">${summaryHTML(c, true)}</aside>`;
  }
  document.addEventListener('change', (e) => {
    const inp = e.target.closest('[data-ci]');
    if (inp) setQty(inp.dataset.ci, parseInt(inp.value, 10) || 0);
  });
  document.addEventListener('click', (e) => {
    const rm = e.target.closest('[data-rm]');
    if (!rm) return;
    const row = rm.closest('.ci');
    const go = () => setQty(rm.dataset.rm, 0);
    if (reduce || !row) return go();
    row.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateX(24px)' }], { duration: 260, easing: 'ease-in' }).onfinish = go;
  });
  document.addEventListener('cart:change', () => { renderCart(); renderCheckout(); });
  renderCart();

  /* ───────── 結帳頁 ───────── */
  const form = $('#co-form');
  function renderCheckout() {
    const box = $('#co-summary');
    if (!box) return;
    const c = read();
    if (!c.length) {
      box.innerHTML = `<div class="cart__empty"><p>${esc(T.empty)}</p><a class="btn btn--navy" href="${D.shopUrl}"><span>${esc(T.toShop)}</span><i aria-hidden="true">›</i></a></div>`;
      if (form) form.hidden = true;
      return;
    }
    const lines = c.map((i) => `<li><img src="${P[i.id].img}" alt=""><span>${esc(P[i.id].name)}<small>× ${i.qty}</small></span><b>${fmt(P[i.id].price * i.qty)}</b></li>`).join('');
    box.innerHTML = `<p class="sum__h">${D.lang === 'ja' ? 'ご注文内容' : '訂單內容'}</p><ul class="sum__lines">${lines}</ul>${summaryHTML(c, false)}<a class="sum__edit" href="${D.cartUrl}">${D.lang === 'ja' ? 'カートを編集' : '修改購物車'} ›</a>`;
  }
  if (form) {
    renderCheckout();
    const comp = $('.co__company');
    form.addEventListener('change', (e) => {
      if (e.target.name === 'invoice_type') {
        comp.hidden = e.target.value !== 'company';
        $('#f-taxid').required = $('#f-title').required = e.target.value === 'company';
      }
    });
    form.addEventListener('submit', (e) => {
      const err = $('.co__err');
      const c = read();
      form.classList.add('checked');
      if (!c.length || !form.checkValidity()) {
        e.preventDefault();
        err.textContent = D.lang === 'ja' ? '入力内容をご確認ください（赤枠の項目）。' : '請確認標示紅框的欄位。';
        err.hidden = false;
        const bad = form.querySelector(':invalid');
        if (bad) { bad.focus({ preventScroll: true }); bad.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' }); }
        return;
      }
      err.hidden = true;
      $('#co-items').value = JSON.stringify(c.map((i) => ({ id: i.id, qty: i.qty })));
      if (D.mode === 'ecpay') {
        const b = form.querySelector('.buy');
        b.disabled = true;
        b.classList.add('loading');
        return; // 交給 api/checkout.php → 綠界
      }
      // 無後端：產生訂單內容，請顧客來電／LINE 確認
      e.preventDefault();
      const d = new Date();
      const pad = (n) => String(n).padStart(2, '0');
      const no = 'YS' + String(d.getFullYear()).slice(2) + pad(d.getMonth() + 1) + pad(d.getDate()) + pad(d.getHours()) + pad(d.getMinutes()) + String(Math.floor(Math.random() * 90) + 10);
      const v = (id) => ($(id) ? $(id).value.trim() : '');
      const { sub, sh, total } = totals(c);
      const inv = form.elements.invoice_type.value === 'company' ? `公司　統編 ${v('#f-taxid')}　抬頭 ${v('#f-title')}` : '個人';
      const text = ['【札幌湯匠 冷凍調理包訂單】', '訂單編號：' + no, '',
        ...c.map((i) => `${P[i.id].name} × ${i.qty}　${fmt(P[i.id].price * i.qty)}`), '',
        '商品小計：' + fmt(sub), '運費：' + (sh == null ? '請告知' : sh === 0 ? '免運' : fmt(sh)), sh == null ? '' : '合計：' + fmt(total), '',
        '收件人：' + v('#f-name'), '電話：' + v('#f-phone'), 'Email：' + v('#f-email'), '地址：' + v('#f-city') + v('#f-address'),
        '希望到貨：' + v('#f-time'), '發票：' + inv, v('#f-note') ? '備註：' + v('#f-note') : ''].filter((x, k, arr) => x !== '' || arr[k - 1] !== '').join('\n');
      $('#co-no').textContent = no;
      $('#co-text').value = text;
      $('.co').hidden = true;
      const done = $('#co-done');
      done.hidden = false;
      done.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    });
    const copy = $('#co-copy');
    if (copy) copy.addEventListener('click', () => {
      const ta = $('#co-text');
      const fallback = () => { ta.focus(); ta.select(); toast(esc(T.copyFail)); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(ta.value).then(() => toast(esc(T.copied)), fallback);
      else fallback();
    });
  }

  /* ───────── 訂單完成頁 ───────── */
  const done = $('#done');
  if (done) {
    const q = new URLSearchParams(location.search);
    const s = q.get('s');
    const no = (q.get('no') || '').replace(/[^A-Za-z0-9]/g, '');
    if (s && done.dataset[s]) $('#done-msg').textContent = done.dataset[s];
    if (no) { const n = $('#done-no'); n.textContent = T.orderNo + '　' + no; n.hidden = false; }
    if (s === 'paid' || s === 'await') write([]);
    done.classList.toggle('done--failed', s === 'failed');
  }

  /* ───────── 主視覺輪播 ───────── */
  const car = $('.car');
  if (car) {
    const slides = $$('.slide', car);
    const dots = $$('.car__dot', car);
    let i = 0;
    let timer = null;
    const DUR = 7000;
    const go = (n, user) => {
      i = (n + slides.length) % slides.length;
      slides.forEach((s, k) => {
        const on = k === i;
        s.classList.toggle('is-on', on);
        s.setAttribute('aria-hidden', on ? 'false' : 'true');
        s.inert = !on;
      });
      dots.forEach((d, k) => { if (k === i) d.setAttribute('aria-current', 'true'); else d.removeAttribute('aria-current'); });
      if (user) play();
    };
    const play = () => {
      if (reduce) return;
      clearInterval(timer);
      car.classList.remove('paused');
      car.style.setProperty('--dur', DUR + 'ms');
      dots.forEach((d) => { d.classList.remove('run'); void d.offsetWidth; });
      if (dots[i]) dots[i].classList.add('run');
      timer = setInterval(() => { go(i + 1); dots.forEach((d) => d.classList.remove('run')); void car.offsetWidth; if (dots[i]) dots[i].classList.add('run'); }, DUR);
    };
    const pause = () => { clearInterval(timer); car.classList.add('paused'); };
    dots.forEach((d, k) => d.addEventListener('click', () => go(k, true)));
    $$('.car__nav', car).forEach((b) => b.addEventListener('click', () => go(i + +b.dataset.dir, true)));
    car.addEventListener('mouseenter', pause);
    car.addEventListener('mouseleave', play);
    car.addEventListener('focusin', pause);
    car.addEventListener('focusout', play);
    document.addEventListener('visibilitychange', () => (document.hidden ? pause() : play()));
    let x0 = null;
    car.addEventListener('pointerdown', (e) => { x0 = e.clientX; });
    car.addEventListener('pointerup', (e) => { if (x0 !== null && Math.abs(e.clientX - x0) > 50) go(i + (e.clientX < x0 ? 1 : -1), true); x0 = null; });
    go(0);
    play();
  }

  /* ───────── 文字逐字浮現（如湯氣） ───────── */
  function split(el) {
    let k = 0;
    const walk = (node) => {
      Array.from(node.childNodes).forEach((n) => {
        if (n.nodeType === 3) {
          const frag = document.createDocumentFragment();
          Array.from(n.textContent).forEach((ch) => {
            if (!ch.trim()) { frag.appendChild(document.createTextNode(ch)); return; }
            const s = document.createElement('span');
            s.className = 'ch';
            s.style.setProperty('--i', k++);
            s.textContent = ch;
            frag.appendChild(s);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1 && n.tagName !== 'BR') walk(n);
      });
    };
    el.setAttribute('aria-label', el.textContent.trim());
    walk(el);
    $$('.ch', el).forEach((c) => c.setAttribute('aria-hidden', 'true'));
  }

  /* ───────── 捲動進場、數字跳動、視差 ───────── */
  if (!reduce && 'IntersectionObserver' in window) {
    root.classList.add('anim');
    $$('.split').forEach(split);
    const sel = '.sh, .tile, .ptile, .ruler__row, .quote__txt, .gift__head, .evt > *, .store__card, .store__img, .news__item, .faq__cat, .cm li, .steps li, .tate, .tate-sec__img, .togo, .pd, .aged > *, .veg, .cat > *, .legal, .two > div, .done, .tbl, .flow, .bt, .rail, .also > *, .gal > figure, .popinfo, .bento__tag, .pick li, .mcat__i, .shopcard, .craft li, .band, .smap__b, .notes, .subh, .area, .nfil';
    const els = $$(sel);
    els.forEach((el) => {
      const sib = el.parentElement ? Array.from(el.parentElement.children).indexOf(el) : 0;
      el.style.setProperty('--d', (sib % 4) * 90 + 'ms');
      if (el.getBoundingClientRect().top > window.innerHeight * 0.92) el.classList.add('rv');
    });
    const countUp = (b) => {
      const to = parseFloat(b.dataset.to);
      const t0 = performance.now();
      const step = (now) => {
        const p = Math.min(1, (now - t0) / 1400);
        b.textContent = Math.round(to * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        const el = en.target;
        el.classList.add('in');
        $$('[data-to]', el).forEach(countUp);
        $$('.split', el).forEach((s) => s.classList.add('go'));
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    $$('.rv').forEach((el) => io.observe(el));
    // 保險：快速捲動或跳轉時，已經捲過的元素一律顯示
    let sweep = 0;
    const reveal = (el) => { el.classList.add('in'); $$('[data-to]', el).forEach(countUp); $$('.split', el).forEach((s) => s.classList.add('go')); io.unobserve(el); };
    window.addEventListener('scroll', () => {
      clearTimeout(sweep);
      sweep = setTimeout(() => $$('.rv:not(.in)').forEach((el) => { if (el.getBoundingClientRect().top < window.innerHeight) reveal(el); }), 120);
    }, { passive: true });
    $$('.split').forEach((s) => { if (!s.closest('.rv')) s.classList.add('go'); });
    window.addEventListener('beforeprint', () => $$('.rv').forEach((el) => el.classList.add('in')));

    // 視差（桌機）
    const par = $$('.quote__img > img, .store__img img, .tate-sec__img img');
    if (par.length && window.matchMedia('(min-width: 901px)').matches) {
      let ticking = false;
      const update = () => {
        const vh = window.innerHeight;
        par.forEach((img) => {
          const r = img.parentElement.getBoundingClientRect();
          if (r.bottom < 0 || r.top > vh) return;
          img.style.transform = `translate3d(0, ${((r.top + r.height / 2 - vh / 2) * -0.07).toFixed(1)}px, 0) scale(1.1)`;
        });
        ticking = false;
      };
      window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
      update();
    }
  }

  /* ───────── 橫向商品軌道（按鈕、進度條、滑鼠拖曳） ───────── */
  $$('[data-rail]').forEach((rail) => {
    const tr = $('.rail__track', rail);
    const bar = $('.rail__bar i', rail);
    const [prev, next] = $$('.rail__btn', rail);
    const upd = () => {
      const max = tr.scrollWidth - tr.clientWidth;
      const vis = Math.min(1, tr.clientWidth / tr.scrollWidth);
      const p = max > 0 ? tr.scrollLeft / max : 0;
      bar.style.width = (vis * 100).toFixed(2) + '%';
      bar.style.left = (p * (1 - vis) * 100).toFixed(2) + '%';
      prev.disabled = tr.scrollLeft <= 2;
      next.disabled = tr.scrollLeft >= max - 2;
      rail.classList.toggle('rail--fit', max <= 2);
    };
    [prev, next].forEach((b) => b.addEventListener('click', () => {
      const it = $('.rail__item', tr);
      const gap = parseFloat(getComputedStyle(tr).columnGap) || 0;
      const step = it ? it.getBoundingClientRect().width + gap : tr.clientWidth * 0.8;
      const n = Math.max(1, Math.floor(tr.clientWidth / step) - 1);
      tr.scrollBy({ left: step * n * Number(b.dataset.dir), behavior: reduce ? 'auto' : 'smooth' });
    }));
    tr.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    let drag = null;
    let suppress = false;
    tr.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      drag = { x: e.clientX, s: tr.scrollLeft, moved: false };
    });
    window.addEventListener('pointermove', (e) => {
      if (!drag) return;
      const dx = e.clientX - drag.x;
      if (!drag.moved && Math.abs(dx) > 5) { drag.moved = true; tr.classList.add('is-drag'); }
      if (drag.moved) tr.scrollLeft = drag.s - dx;
    });
    window.addEventListener('pointerup', () => {
      if (!drag) return;
      if (drag.moved) { suppress = true; setTimeout(() => { suppress = false; }, 60); }
      drag = null;
      tr.classList.remove('is-drag');
    });
    tr.addEventListener('click', (e) => { if (suppress) { e.preventDefault(); e.stopPropagation(); } }, true);
    tr.addEventListener('dragstart', (e) => e.preventDefault());
    upd();
  });

  /* ───────── 頁內分類分頁：捲動時標示目前區塊 ───────── */
  $$('[data-ctab]').forEach((bar) => {
    const links = $$('a[href*="#"]', bar).filter((a) => {
      const u = new URL(a.href, location.href);
      return u.pathname === location.pathname && u.hash.length > 1 && document.getElementById(decodeURIComponent(u.hash.slice(1)));
    });
    if (!links.length) return;
    const secs = links.map((a) => document.getElementById(decodeURIComponent(new URL(a.href, location.href).hash.slice(1))));
    const ul = $('ul', bar);
    let curr = -1;
    const mark = () => {
      const line = bar.getBoundingClientRect().bottom + 24;
      let k = -1;
      secs.forEach((sec, i) => { if (sec.getBoundingClientRect().top <= line) k = i; });
      if (k === curr) return;
      curr = k;
      links.forEach((a, i) => { if (i === k) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); });
      const on = links[k];
      if (on && ul.scrollWidth > ul.clientWidth) ul.scrollTo({ left: on.offsetLeft - ul.clientWidth / 2 + on.offsetWidth / 2, behavior: reduce ? 'auto' : 'smooth' });
    };
    let raf = 0;
    window.addEventListener('scroll', () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; mark(); }); }, { passive: true });
    mark();
  });

  /* ───────── 最新消息分類篩選 ───────── */
  const nfil = $('.nfil');
  if (nfil) {
    const items = $$('.news__item[data-c]');
    nfil.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-f]');
      if (!b) return;
      $$('button', nfil).forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      const f = b.dataset.f;
      items.forEach((it) => {
        const show = f === 'all' || it.dataset.c === f;
        it.classList.toggle('is-out', !show);
        it.classList.remove('is-in');
        if (show && !reduce) { void it.offsetWidth; it.classList.add('is-in'); }
      });
    });
  }

  /* ───────── 商品介紹：分類篩選、搜尋、排序、快速檢視 ───────── */
  const plist = $('[data-plist]');
  if (plist) {
    const grid = $('[data-pgrid]', plist);
    const cards = $$('.pc', grid);
    const order = cards.slice();
    const side = $('.pside', plist);
    const labels = JSON.parse(plist.dataset.labels || '{}');
    const KEYS = ['cat', 'ing', 'buy', 'tag'];
    const st = { cat: '', ing: '', buy: '', tag: '', q: '', sort: 'rec' };
    const qIn = $('[data-psearch] input', plist);
    const sortSel = $('[data-psort]', plist);
    const listSec = $('#list');
    const fromHash = (h) => {
      const raw = (h || '').replace(/^#/, '');
      if (raw.indexOf('=') < 0) return false;
      const p = new URLSearchParams(raw);
      KEYS.forEach((k) => { st[k] = p.get(k) || ''; });
      st.q = p.get('q') || '';
      return true;
    };
    const toHash = () => {
      const p = new URLSearchParams();
      KEYS.forEach((k) => { if (st[k]) p.set(k, st[k]); });
      if (st.q) p.set('q', st.q);
      const str = p.toString();
      try { history.replaceState(null, '', str ? '#' + str : location.pathname + location.search); } catch (e) { /* 預覽環境 */ }
    };
    const apply = (animate) => {
      const q = st.q.trim().toLowerCase();
      let n = 0;
      cards.forEach((c) => {
        const ok = (!st.cat || c.dataset.cat === st.cat) && (!st.ing || c.dataset.ing === st.ing)
          && (!st.buy || c.dataset.buy.split(' ').includes(st.buy)) && (!st.tag || c.dataset.tags.split(' ').includes(st.tag))
          && (!q || c.dataset.q.includes(q));
        c.hidden = !ok;
        c.classList.remove('is-in');
        if (ok) { n += 1; if (animate && !reduce) { void c.offsetWidth; c.classList.add('is-in'); } }
      });
      const pr = (c) => (c.dataset.price === '' ? null : +c.dataset.price);
      const sorted = st.sort === 'rec' ? order : order.slice().sort((a, b) => {
        const x = pr(a), y = pr(b);
        if (x == null && y == null) return 0;
        if (x == null) return 1;
        if (y == null) return -1;
        return st.sort === 'asc' ? x - y : y - x;
      });
      sorted.forEach((c) => grid.appendChild(c));
      $('[data-pcount]', plist).textContent = n;
      $('[data-pempty]', plist).hidden = n > 0;
      const pq = $('[data-pq]', plist);
      pq.hidden = !q;
      if (q) pq.textContent = (document.documentElement.lang === 'ja' ? '「' + st.q + '」の検索結果' : '「' + st.q + '」的搜尋結果');
      $$('[data-k]', side).forEach((a) => {
        const on = (st[a.dataset.k] || '') === a.dataset.v;
        if (on) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
      });
      const chips = $('[data-pchips]', plist);
      chips.innerHTML = KEYS.filter((k) => st[k]).map((k) => `<button type="button" class="fchip" data-clear="${k}">${esc((labels[k] || {})[st[k]] || st[k])}<i aria-hidden="true">×</i></button>`).join('')
        + (st.q ? `<button type="button" class="fchip" data-clear="q">${esc(st.q)}<i aria-hidden="true">×</i></button>` : '');
      if (qIn && qIn.value !== st.q) qIn.value = st.q;
    };
    const toList = () => {
      const h = listSec && $('.sh', listSec);
      if (!h) return;
      const bar = $('.ctab');
      const off = (window.innerWidth > 1080 ? 66 : 64) + (bar ? bar.offsetHeight : 0) + 36;
      window.scrollTo({ top: h.getBoundingClientRect().top + window.scrollY - off, behavior: reduce ? 'auto' : 'smooth' });
    };
    // 側欄分類：同一層再點一次即取消
    side.addEventListener('click', (e) => {
      const a = e.target.closest('[data-k]');
      if (!a) return;
      e.preventDefault();
      const k = a.dataset.k;
      st[k] = a.dataset.v && st[k] !== a.dataset.v ? a.dataset.v : '';
      toHash(); apply(true);
    });
    plist.addEventListener('click', (e) => {
      const c = e.target.closest('[data-clear]');
      if (c) { st[c.dataset.clear] = ''; toHash(); apply(true); return; }
      if (e.target.closest('[data-preset]')) { KEYS.forEach((k) => { st[k] = ''; }); st.q = ''; toHash(); apply(true); }
    });
    const sf = $('[data-psearch]', plist);
    sf.addEventListener('submit', (e) => { e.preventDefault(); st.q = qIn.value.trim(); toHash(); apply(true); });
    let qt = 0;
    qIn.addEventListener('input', () => { clearTimeout(qt); qt = setTimeout(() => { st.q = qIn.value.trim(); toHash(); apply(true); }, 180); });
    sortSel.addEventListener('change', () => { st.sort = sortSel.value; apply(true); });
    // 同頁的分類連結（分類卡、索引、下拉選單）：套用條件並捲到商品列表
    document.addEventListener('click', (e) => {
      const a = e.target.closest('a[href*="#"]');
      if (!a || a.closest('.pside')) return;
      const u = new URL(a.href, location.href);
      if (u.pathname !== location.pathname || u.hash.indexOf('=') < 0) return;
      e.preventDefault();
      KEYS.forEach((k) => { st[k] = ''; }); st.q = '';
      fromHash(u.hash); toHash(); apply(true);
      const it = a.closest('.has-mega');
      if (it) { it.classList.add('is-closed'); a.blur(); }
      setTimeout(toList, 30);
    });
    window.addEventListener('hashchange', () => { if (fromHash(location.hash)) { apply(true); toList(); } });
    if (fromHash(location.hash)) { apply(false); setTimeout(toList, 120); } else apply(false);

    // 快速檢視（比照「請選擇規格與數量」視窗）
    const qv = $('#qv');
    const qin = qv && $('[data-qv-in]', qv);
    if (qv && typeof qv.showModal === 'function') {
      grid.addEventListener('click', (e) => {
        const b = e.target.closest('[data-qv]');
        if (!b) return;
        const tpl = document.getElementById('qv-' + b.dataset.qv);
        if (!tpl) return;
        qin.replaceChildren(tpl.content.cloneNode(true));
        qv._from = b.querySelector('img');
        qv.showModal();
        document.body.classList.add('qv-open');
      });
      $('[data-qv-close]', qv).addEventListener('click', () => qv.close());
      qv.addEventListener('click', (e) => { if (e.target === qv) qv.close(); });
      qv.addEventListener('close', () => document.body.classList.remove('qv-open'));
    }
  }
  // 下拉選單點選後先收起，滑鼠離開再恢復
  $$('.has-mega').forEach((it) => {
    $$('.mega a', it).forEach((a) => a.addEventListener('click', () => { it.classList.add('is-closed'); a.blur(); }));
    it.addEventListener('mouseenter', () => it.classList.remove('is-closed'));
    $('.gnav__a', it).addEventListener('focus', () => it.classList.remove('is-closed'));
  });

  /* ───────── 頁首、回到頂端 ───────── */
  const hd = $('.hd');
  const top = $('.totop');
  let lastY = 0;
  const onScroll = () => {
    const y = window.scrollY;
    if (hd) hd.classList.toggle('hd--stuck', y > 140);
    if (top) top.hidden = y < 700;
    document.body.classList.toggle('scrolling-down', y > lastY && y > 300);
    lastY = y;
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (top) top.addEventListener('click', () => window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' }));

  // 選單開啟時鎖住背景捲動；點選連結後收起
  const navT = $('#nav-t');
  if (navT) {
    navT.addEventListener('change', () => document.body.classList.toggle('nav-open', navT.checked));
    $$('.gnav a').forEach((a) => a.addEventListener('click', () => { navT.checked = false; document.body.classList.remove('nav-open'); }));
    document.addEventListener('keydown', (e) => {
      if (e.key !== 'Escape') return;
      if (navT.checked) { navT.checked = false; document.body.classList.remove('nav-open'); }
      const a = document.activeElement;
      if (a && a.closest && a.closest('.has-mega')) a.blur();
    });
  }

  /* ───────── 換頁淡出 ───────── */
  if (!reduce) {
    root.classList.add('ready');
    document.addEventListener('click', (e) => {
      const a = e.target.closest('a[href]');
      if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const href = a.getAttribute('href');
      if (!href || href.startsWith('#') || a.target === '_blank' || /^(https?:|tel:|mailto:)/.test(href) || a.hasAttribute('download')) return;
      const to = new URL(a.href, location.href);
      if (to.pathname === location.pathname && to.search === location.search && to.hash) return; // 同頁錨點：直接捲動
      e.preventDefault();
      root.classList.add('leaving');
      setTimeout(() => { location.href = a.href; }, 260);
    });
    window.addEventListener('pageshow', () => root.classList.remove('leaving'));
  }
})();
