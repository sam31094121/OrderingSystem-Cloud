const socket = io();
let menu = [];
let cart = [];

socket.on('connect', () => {
    console.log('Connected to server');
});

const statusTranslations = {
    'pending': '待處理',
    'received': '已接單',
    'cooking': '烹調中',
    'ready': '已完成',
    'completed': '已送達'
};

socket.on('order_updated', (order) => {
    console.log('Order updated:', order);
    const statusText = statusTranslations[order.status] || order.status;
    showNotification(`訂單 ${order.order_number} 狀態：${statusText}`, 'info');
});

async function loadMenu() {
    try {
        const response = await fetch('/api/menu');
        menu = await response.json();
        displayMenu();
    } catch (error) {
        console.error('Error loading menu:', error);
        showNotification('載入菜單時發生錯誤', 'danger');
    }
}

function displayMenu() {
    const container = document.getElementById('menu-container');
    const categories = [...new Set(menu.map(item => item.category))];
    
    let html = '';
    
    categories.forEach(category => {
        html += `<div class="col-12 mt-3"><h5 class="text-muted">${category}</h5></div>`;
        
        const items = menu.filter(item => item.category === category);
        items.forEach(item => {
            html += `
                <div class="col-md-6 col-lg-4">
                    <div class="menu-item" onclick="addToCart(${item.id})">
                        <h5>${item.name}</h5>
                        <div class="price">$${item.price.toFixed(2)}</div>
                        <div class="description">${item.description || ''}</div>
                        <span class="category">${item.category}</span>
                    </div>
                </div>
            `;
        });
    });
    
    container.innerHTML = html;
}

function addToCart(itemId) {
    const menuItem = menu.find(item => item.id === itemId);
    if (!menuItem) return;
    
    const existingItem = cart.find(item => item.id === itemId);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: menuItem.id,
            name: menuItem.name,
            price: menuItem.price,
            quantity: 1
        });
    }
    
    updateCart();
    showNotification(`已將 ${menuItem.name} 加入購物車`, 'success');
}

function updateCart() {
    const container = document.getElementById('cart-items');
    const submitBtn = document.getElementById('submit-order-btn');
    
    if (cart.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-4">購物車是空的。請從菜單新增項目。</p>';
        submitBtn.disabled = true;
        updateTotal();
        return;
    }
    
    let html = '';
    cart.forEach((item, index) => {
        html += `
            <div class="cart-item">
                <div class="cart-item-header">
                    <strong>${item.name}</strong>
                    <button class="btn btn-sm btn-danger" onclick="removeFromCart(${index})">
                        <small>✕</small>
                    </button>
                </div>
                <div class="cart-item-controls">
                    <button class="btn btn-sm btn-outline-secondary qty-btn" onclick="decreaseQuantity(${index})">-</button>
                    <span class="quantity">${item.quantity}</span>
                    <button class="btn btn-sm btn-outline-secondary qty-btn" onclick="increaseQuantity(${index})">+</button>
                    <span class="ms-auto text-success fw-bold">$${(item.price * item.quantity).toFixed(2)}</span>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    submitBtn.disabled = false;
    updateTotal();
}

function increaseQuantity(index) {
    cart[index].quantity += 1;
    updateCart();
}

function decreaseQuantity(index) {
    if (cart[index].quantity > 1) {
        cart[index].quantity -= 1;
        updateCart();
    }
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCart();
}

function updateTotal() {
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    document.getElementById('cart-total').textContent = `$${total.toFixed(2)}`;
}

function clearCart() {
    cart = [];
    updateCart();
    document.getElementById('order-notes').value = '';
}

async function submitOrder() {
    if (cart.length === 0) {
        showNotification('購物車是空的！', 'warning');
        return;
    }
    
    const notes = document.getElementById('order-notes').value;
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    const orderData = {
        items: cart.map(item => ({
            id: item.id,
            name: item.name,
            price: item.price,
            quantity: item.quantity
        })),
        total_amount: total,
        notes: notes
    };
    
    try {
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        document.getElementById('modal-order-number').textContent = result.order_number;
        const modal = new bootstrap.Modal(document.getElementById('orderSuccessModal'));
        modal.show();
        
        clearCart();
        
    } catch (error) {
        console.error('Error submitting order:', error);
        showNotification('送出訂單時發生錯誤', 'danger');
    }
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('order-status');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    container.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 3000);
}

document.getElementById('submit-order-btn').addEventListener('click', submitOrder);
document.getElementById('clear-cart-btn').addEventListener('click', clearCart);

loadMenu();
