async function api(path, opts={}){
  const res = await fetch('/api' + path, opts);
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadItems(){
  const items = await api('/items');
  const container = document.getElementById('inventory');
  let html = '<table><thead><tr><th>ID</th><th>Name</th><th>SKU</th><th>Price</th><th>Qty</th></tr></thead><tbody>';
  for(const it of items){
    html += `<tr><td>${it.id}</td><td>${it.name}</td><td>${it.sku||''}</td><td>${it.price}</td><td>${it.quantity}</td></tr>`;
  }
  html += '</tbody></table>';
  container.innerHTML = html;

  // invoice items form
  const invItems = document.getElementById('invoice-items');
  invItems.innerHTML = '';
  for(const it of items){
    const row = document.createElement('div');
    row.className = 'row';
    row.innerHTML = `<div class="col">${it.name} (stock: ${it.quantity})</div><div><input type="number" min="0" value="0" data-item="${it.id}" style="width:80px" /></div>`;
    invItems.appendChild(row);
  }
}

window.addEventListener('DOMContentLoaded', ()=>{
  loadItems().catch(err=>console.error(err));

  document.getElementById('addBtn').addEventListener('click', async ()=>{
    const name = document.getElementById('name').value;
    const sku = document.getElementById('sku').value;
    const price = parseFloat(document.getElementById('price').value || 0);
    const quantity = parseInt(document.getElementById('quantity').value || 0);
    try{
      await api('/items', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name, sku, price, quantity}) });
      await loadItems();
    }catch(e){ alert('Error: '+e.message) }
  });

  document.getElementById('createInvoice').addEventListener('click', async ()=>{
    const customer_name = document.getElementById('customer_name').value;
    const customer_email = document.getElementById('customer_email').value;
    const inputs = document.querySelectorAll('#invoice-items input[type=number]');
    const items = [];
    for(const inp of inputs){
      const qty = parseInt(inp.value||0);
      if(qty>0){ items.push({ item_id: parseInt(inp.dataset.item), quantity: qty }) }
    }
    if(items.length===0){ alert('Select at least one item'); return }
    try{
      const inv = await api('/invoices', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ customer_name, customer_email, items }) });
      alert('Invoice created. ID: '+inv.id+' Total: '+inv.total);
      document.getElementById('customer_name').value='';
      document.getElementById('customer_email').value='';
      await loadItems();
      loadInvoices();
    }catch(e){ alert('Error: '+e.message) }
  });

  async function loadInvoices(){
    const invoices = await api('/invoices');
    const container = document.getElementById('invoices');
    let html = '<ul>';
    for(const inv of invoices){ html += `<li>Invoice ${inv.id} - Total: ${inv.total} - Customer ID: ${inv.customer_id || 'n/a'}</li>` }
    html += '</ul>';
    container.innerHTML = html;
  }
  window.loadInvoices = loadInvoices;
  loadInvoices();
});
