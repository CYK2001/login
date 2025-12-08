// 通用API调用函数
export async function apiCall(url, method = 'GET', data = null, isFormData = false) {
    try {
        const options = {
            method: method
        };
        
        // 从localStorage获取auth_token并添加到请求头
        const authToken = getAuthToken();
        if (authToken) {
            options.headers = options.headers || {};
            options.headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        let requestUrl = url;
        
        // 处理请求参数
        if (data) {
            if (method.toUpperCase() === 'GET' || method.toUpperCase() === 'HEAD') {
                // GET/HEAD请求：将参数转换为查询字符串
                const params = new URLSearchParams();
                for (const key in data) {
                    if (data.hasOwnProperty(key) && data[key] !== undefined && data[key] !== null && data[key] !== '') {
                        params.append(key, data[key]);
                    }
                }
                const queryString = params.toString();
                if (queryString) {
                    requestUrl += (requestUrl.includes('?') ? '&' : '?') + queryString;
                }
            } else {
                // POST/PUT等请求：将参数作为请求体
                if (isFormData || data instanceof FormData) {
                    options.body = data;
                    // 不需要设置Content-Type，浏览器会自动设置
                } else {
                    // 确保设置Content-Type为JSON
                    options.headers = options.headers || {};
                    options.headers['Content-Type'] = 'application/json';
                    options.body = JSON.stringify(data);
                }
            }
        }
        
        const response = await fetch(requestUrl, options);
        
        // 处理响应
        let result;
        try {
            result = await response.json();
        } catch (jsonError) {
            // 如果响应不是JSON格式，抛出错误
            throw new Error('服务器响应格式错误');
        }
        
        if (!response.ok) {
            throw new Error(result.msg || '请求失败');
        }
        
        return result;
    } catch (error) {
        // 静默处理错误
        throw error;
    }
}

// 密码可见性切换函数
export function togglePasswordVisibility(inputId) {
    const passwordInput = document.getElementById(inputId);
    if (!passwordInput) return;
    
    // 查找相邻的密码切换按钮
    const toggleBtn = passwordInput.parentElement.querySelector('.password-toggle');
    
    // 切换密码可见性
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        // 更新按钮图标 - 密码可见时显示正常眼睛
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
            toggleBtn.title = '隐藏密码';
            toggleBtn.setAttribute('aria-label', '隐藏密码');
        }
    } else {
        passwordInput.type = 'password';
        // 更新按钮图标 - 密码隐藏时显示带斜线的眼睛
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>';
            toggleBtn.title = '显示密码';
            toggleBtn.setAttribute('aria-label', '显示密码');
        }
    }
}

// 初始化所有密码输入框的可见性切换功能
export function initPasswordToggle() {
    // 为所有密码输入框初始化
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        // 查找相邻的密码切换按钮
        const toggleBtn = input.parentElement.querySelector('.password-toggle');
        
        if (toggleBtn) {
            // 确保按钮初始状态为带斜线的眼睛图标（密码默认隐藏）
            toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>';
            toggleBtn.title = '显示密码';
            toggleBtn.setAttribute('aria-label', '显示密码');
        }
    });
}

// 通用工具函数：创建模态框元素
function createModalElement(type, category, position) {
    // 设置不同类型的颜色
    const colors = {
        success: { border: '#4CAF50', background: '#4CAF50', iconBg: '#4CAF50' },
        error: { border: '#f44336', background: '#f44336', iconBg: '#f44336' },
        warning: { border: '#ff9800', background: '#ff9800', iconBg: '#ff9800' },
        info: { border: '#2196F3', background: '#2196F3', iconBg: '#2196F3' }
    };
    
    const color = colors[category] || (type === 'confirm' ? colors.warning : colors.info);
    
    // 创建弹窗元素
    const modal = document.createElement('div');
    
    // 根据弹窗类型设置不同的样式
    const baseStyle = `
        background: #fff;
        border: 1px solid ${color.border};
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        opacity: 0;
        transition: all 0.3s ease;
        padding: ${type === 'confirm' ? '16px' : '12px'};
    `;
    
    if (type === 'confirm') {
        modal.style.cssText = `${baseStyle}
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0.9);
            min-width: 300px;
            max-width: 500px;
        `;
    } else {
        modal.style.cssText = `${baseStyle}
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translate(-50%, -20px);
            min-width: 300px;
            max-width: 500px;
        `;
    }
    
    return modal;
}

// 通用工具函数：创建消息内容
function createMessageContent(message, category, type) {
    // 创建消息容器
    const messageContainer = document.createElement('div');
    messageContainer.style.cssText = `
        display: flex;
        align-items: ${type === 'confirm' ? 'flex-start' : 'center'};
        ${type === 'confirm' ? 'margin-bottom: 16px;' : ''}
    `;
    
    // 创建图标
    const icon = document.createElement('span');
    icon.style.cssText = `
        display: inline-block;
        width: 24px;
        height: 24px;
        background: ${getColorByCategory(category).background};
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 24px;
        font-size: 14px;
        margin-right: 10px;
        ${type === 'confirm' ? 'flex-shrink: 0;' : ''}
    `;
    
    // 根据消息类型设置图标
    if (category === 'success') {
        icon.textContent = '✓';
    } else if (category === 'error') {
        icon.textContent = '✗';
    } else if (category === 'warning') {
        icon.textContent = '!';
    } else {
        icon.textContent = 'i';
    }
    
    // 创建消息文本
    const messageText = document.createElement(type === 'confirm' ? 'div' : 'span');
    messageText.style.cssText = `
        font-size: 14px;
        color: #333;
        ${type === 'confirm' ? 'line-height: 1.4; flex: 1;' : 'flex: 1;'}
    `;
    messageText.textContent = message;
    
    // 组装消息内容
    messageContainer.appendChild(icon);
    messageContainer.appendChild(messageText);
    
    return messageContainer;
}

// 通用工具函数：获取颜色配置
function getColorByCategory(category) {
    const colors = {
        success: { border: '#4CAF50', background: '#4CAF50', iconBg: '#4CAF50' },
        error: { border: '#f44336', background: '#f44336', iconBg: '#f44336' },
        warning: { border: '#ff9800', background: '#ff9800', iconBg: '#ff9800' },
        info: { border: '#2196F3', background: '#2196F3', iconBg: '#2196F3' }
    };
    
    return colors[category] || colors.info;
}

// 通用工具函数：创建关闭按钮
function createCloseButton(modal, type, onClose) {
    const closeBtn = document.createElement('button');
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: #999;
        font-size: 16px;
        cursor: pointer;
        padding: 2px;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    closeBtn.textContent = '×';
    
    // 关闭按钮事件
    closeBtn.addEventListener('click', () => {
        closeModal(modal, type);
        if (onClose) onClose();
    });
    
    return closeBtn;
}

// 通用工具函数：关闭模态框
function closeModal(modal, type) {
    if (type === 'confirm') {
        modal.style.opacity = '0';
        modal.style.transform = 'translate(-50%, -50%) scale(0.9)';
    } else {
        modal.style.opacity = '0';
        modal.style.transform = 'translate(-50%, -20px)';
    }
    
    setTimeout(() => {
        modal.remove();
    }, 300);
}

// 通用消息提示函数
export function showMessage(message, category = 'info') {
    // 创建弹窗和消息内容
    const modal = createModalElement('message', category);
    const messageContainer = createMessageContent(message, category, 'message');
    
    // 创建关闭按钮
    const closeBtn = createCloseButton(modal, 'message');
    messageContainer.appendChild(closeBtn);
    
    // 组装弹窗
    modal.appendChild(messageContainer);
    
    // 添加到页面
    document.body.appendChild(modal);
    
    // 显示弹窗
    setTimeout(() => {
        modal.style.opacity = '1';
        modal.style.transform = 'translate(-50%, 0)';
    }, 10);
    
    // 自动关闭
    setTimeout(() => {
        closeModal(modal, 'message');
    }, 3000);
    
    return modal;
}

// 通用确认对话框函数
export function showConfirm(message, category = 'warning') {
    return new Promise((resolve) => {
        const confirmCallback = () => resolve(true);
        const cancelCallback = () => resolve(false);
        
        // 创建弹窗和消息内容
        const modal = createModalElement('confirm', category);
        const messageContainer = createMessageContent(message, category, 'confirm');
        
        // 创建按钮容器
        const buttonContainer = document.createElement('div');
        buttonContainer.style.cssText = `
            display: flex;
            justify-content: flex-end;
            gap: 8px;
        `;
        
        // 获取颜色配置
        const color = getColorByCategory(category);
        
        // 创建取消按钮
        const cancelBtn = document.createElement('button');
        cancelBtn.style.cssText = `
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            color: #333;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
        `;
        cancelBtn.textContent = '取消';
        
        // 创建确认按钮
        const confirmBtn = document.createElement('button');
        confirmBtn.style.cssText = `
            padding: 6px 12px;
            border: 1px solid ${color.border};
            border-radius: 4px;
            background: ${color.background};
            color: white;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
        `;
        confirmBtn.textContent = '确认';
        
        // 按钮事件
        cancelBtn.addEventListener('click', () => {
            closeModal(modal, 'confirm');
            cancelCallback();
        });
        
        confirmBtn.addEventListener('click', () => {
            closeModal(modal, 'confirm');
            confirmCallback();
        });
        
        // 点击模态框外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal, 'confirm');
                cancelCallback();
            }
        });
        
        // 组装弹窗
        buttonContainer.appendChild(cancelBtn);
        buttonContainer.appendChild(confirmBtn);
        modal.appendChild(messageContainer);
        modal.appendChild(buttonContainer);
        
        // 添加到页面
        document.body.appendChild(modal);
        
        // 显示弹窗
        setTimeout(() => {
            modal.style.opacity = '1';
            modal.style.transform = 'translate(-50%, -50%) scale(1)';
        }, 10);
    });
}

// 通用表单验证函数
export function validateForm(formId, rules, showMessage) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    
    // 遍历所有输入字段
    Object.keys(rules).forEach(fieldName => {
        const field = form[fieldName] || document.getElementById(fieldName);
        if (!field) return;
        
        const rule = rules[fieldName];
        const value = field.value.trim();
        let errorMessage = '';
        
        // 必填验证
        if (rule.required && !value) {
            errorMessage = rule.message || '此项为必填';
        } 
        // 最小长度验证
        else if (rule.minLength && value.length < rule.minLength) {
            errorMessage = rule.message || `最少需要${rule.minLength}个字符`;
        } 
        // 最大长度验证
        else if (rule.maxLength && value.length > rule.maxLength) {
            errorMessage = rule.message || `最多只能${rule.maxLength}个字符`;
        } 
        // 邮箱验证
        else if (rule.email && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            errorMessage = rule.message || '请输入有效的邮箱地址';
        } 
        // 手机号码验证
        else if (rule.phone && value && !/^1[3-9]\d{9}$/.test(value)) {
            errorMessage = rule.message || '请输入有效的手机号码';
        } 
        // 两次密码一致验证
        else if (rule.equalTo) {
            const targetField = form[rule.equalTo] || document.getElementById(rule.equalTo);
            if (targetField && value !== targetField.value) {
                errorMessage = rule.message || '两次输入不一致';
            }
        }
        
        // 如果有错误消息，显示并标记为无效
        if (errorMessage) {
            isValid = false;
            showMessage(errorMessage, 'error');
            
            // 设置输入框的样式为错误状态
            field.style.borderColor = '#f44336';
            field.addEventListener('input', function clearError() {
                field.style.borderColor = '';
                field.removeEventListener('input', clearError);
            });
        }
    });
    
    return isValid;
}

// 保存认证token到localStorage
export function setAuthToken(token) {
    localStorage.setItem('auth_token', token);
}

// 从localStorage获取认证token
export function getAuthToken() {
    return localStorage.getItem('auth_token');
}

// 删除localStorage中的认证token
export function removeAuthToken() {
    localStorage.removeItem('auth_token');
}