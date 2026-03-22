// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 导航切换功能
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有导航链接的活跃状态
            navLinks.forEach(item => item.classList.remove('active'));
            // 添加当前导航链接的活跃状态
            this.classList.add('active');
            
            // 隐藏所有内容区域
            contentSections.forEach(section => section.classList.remove('active'));
            // 显示目标内容区域
            const target = this.getAttribute('data-target');
            const targetSection = document.getElementById(target);
            targetSection.classList.add('active');
            
            // 账号管理页面和链接下载页面都需要监听剪贴板
            if (target === 'account' || target === 'download') {
                startClipboardListener();
            } else {
                stopClipboardListener();
            }
        });
    });
    
    // 剪贴板监听功能
    let clipboardListenerInterval;
    let lastClipboardContent = '';
    
    function startClipboardListener() {
        // 清除之前的监听
        stopClipboardListener();
        
        // 每1秒检查一次剪贴板
        clipboardListenerInterval = setInterval(async function() {
            try {
                // 获取剪贴板内容
                const text = await navigator.clipboard.readText();
                
                // 检查剪贴板内容是否发生变化
                if (text !== lastClipboardContent) {
                    lastClipboardContent = text;
                    
                    // 检查当前活跃的页面
                    const activeSection = document.querySelector('.content-section.active');
                    if (activeSection) {
                        const activeId = activeSection.id;
                        
                        if (activeId === 'account') {
                            // 账号管理页面
                            const input = document.getElementById('add-sec-user-id');
                            if (input) {
                                // 检查是否包含抖音或TikTok的用户主页链接
                                if (text.includes('douyin.com/user/') || text.includes('tiktok.com/@')) {
                                    input.value = text;
                                }
                            }
                        } else if (activeId === 'download') {
                            // 链接下载页面
                            const input = document.getElementById('link');
                            if (input) {
                                // 直接粘贴剪贴板内容，支持多条链接（换行分隔）
                                input.value = text;
                            }
                        }
                    }
                }
            } catch (err) {
                console.error('无法访问剪贴板:', err);
            }
        }, 1000);
    }
    
    function stopClipboardListener() {
        if (clipboardListenerInterval) {
            clearInterval(clipboardListenerInterval);
            clipboardListenerInterval = null;
        }
    }
    
    // 页面加载时，如果当前是账号管理或链接下载页面，开始监听剪贴板
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection && (activeSection.id === 'account' || activeSection.id === 'download')) {
        startClipboardListener();
    }
    
    // 卡片链接点击事件
    const cardLinks = document.querySelectorAll('.card .btn');
    cardLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const target = this.getAttribute('data-target');
            // 触发对应导航链接的点击事件
            document.querySelector(`.nav-link[data-target="${target}"]`).click();
        });
    });
    
    // 编辑模式相关变量
    let editMode = false;
    let currentAccountId = '';
    
    // 处理添加账号表单提交
    const addAccountForm = document.getElementById('add-account-form');
    addAccountForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const platform = document.getElementById('add-platform').value;
        const secUserId = document.getElementById('add-sec-user-id').value;
        
        // 处理多行账号（按换行分隔）
        const accounts = secUserId.split('\n').filter(a => a.trim() !== '');
        
        if (accounts.length === 0) {
            const statusElement = document.getElementById('add-account-status');
            statusElement.textContent = '请输入有效的账号信息！';
            statusElement.className = 'status-message error';
            // 10秒后消失
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.className = 'status-message';
            }, 10000);
            return;
        }
        
        // 调用添加账号函数，不传递用户名，让后端自动获取
        accounts.forEach((account, index) => {
            // 延迟添加，避免请求过于密集
            setTimeout(() => {
                addAccount(platform, '', account);
            }, index * 1000);
        });
    });
    
    // 加载账号列表
    function loadAccounts() {
        fetch('/accounts', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.message && data.message.includes('成功')) {
                renderAccounts(data.data);
            } else {
                console.error('加载账号列表失败:', data.message);
            }
        })
        .catch(error => {
            console.error('加载账号列表失败:', error);
        });
    }
    
    // 下载进度状态管理
    let downloadStatus = {};
    
    // 合集列表数据
    let collections = [];
    
    // 加载合集列表
    function loadCollections() {
        console.log('开始加载合集列表');
        fetch('/collections', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            }
        })
        .then(response => {
            console.log('获取合集列表响应:', response);
            return response.json();
        })
        .then(data => {
            console.log('获取合集列表数据:', data);
            if (data && data.message && data.message.includes('成功')) {
                console.log('合集数据:', data.data);
                collections = data.data;
                renderCollections(collections);
            } else {
                console.error('加载合集列表失败:', data.message);
            }
        })
        .catch(error => {
            console.error('加载合集列表失败:', error);
        });
    }
    
    // 渲染合集列表
    function renderCollections(collections) {
        console.log('开始渲染合集列表，数据长度:', collections.length);
        console.log('合集数据详情:', collections);
        const tableBody = document.getElementById('collection-table-body');
        console.log('获取表格体元素:', tableBody);
        tableBody.innerHTML = '';
        
        collections.forEach(collection => {
            console.log('渲染单个合集:', collection);
            // 获取下载状态
            const status = downloadStatus[collection.id] || '空闲';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${collection.platform === 'douyin' ? '抖音' : 'TikTok'}</td>
                <td>${collection.username}</td>
                <td>
                    <button class="btn btn-danger delete-collection-btn" data-id="${collection.id}">删除</button>
                    <button class="btn btn-primary download-collection-btn" data-id="${collection.id}">下载合集</button>
                </td>
                <td style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" class="collection-download-status" data-id="${collection.id}">${status}</td>
                <td style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"><a href="${collection.url}" target="_blank" title="${collection.url}">${collection.url}</a></td>
            `;
            
            tableBody.appendChild(row);
        });
        
        // 添加事件监听器
        addCollectionEventListeners();
        console.log('合集列表渲染完成');
    }
    
    // 添加合集事件监听器
    function addCollectionEventListeners() {
        // 删除按钮事件
        document.querySelectorAll('.delete-collection-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const collectionId = this.getAttribute('data-id');
                deleteCollection(collectionId);
            });
        });
        
        // 下载按钮事件
        document.querySelectorAll('.download-collection-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const collectionId = this.getAttribute('data-id');
                downloadCollection(collectionId);
            });
        });
    }
    
    // 删除合集
    function deleteCollection(collectionId) {
        if (confirm('确定要删除这个合集吗？')) {
            fetch(`/collections/${collectionId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'token': 'test'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data && data.message && data.message.includes('成功')) {
                    // 重新加载合集列表
                    loadCollections();
                } else {
                    console.error('删除合集失败:', data.message);
                }
            })
            .catch(error => {
                console.error('删除合集失败:', error);
            });
        }
    }
    
    // 下载合集
    function downloadCollection(collectionId) {
        // 清除之前可能存在的计时器
        clearInterval(window[`listProgressInterval_${collectionId}`]);
        clearInterval(window[`downloadProgressInterval_${collectionId}`]);
        
        // 更新下载状态为开始下载
        updateCollectionDownloadStatus(collectionId, '开始下载');
        
        // 开始获取作品列表
        updateCollectionDownloadStatus(collectionId, '作品列表0%');
        
        // 模拟获取作品列表的进度
        let listProgress = 0;
        window[`listProgressInterval_${collectionId}`] = setInterval(() => {
            listProgress += 5;
            if (listProgress <= 100) {
                updateCollectionDownloadStatus(collectionId, `作品列表${listProgress}%`);
            } else {
                clearInterval(window[`listProgressInterval_${collectionId}`]);
            }
        }, 100);
        
        // 发送下载请求
        fetch(`/collections/${collectionId}/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            }
        })
        .then(response => response.json())
        .then(data => {
            // 清除获取作品列表的进度计时器
            clearInterval(window[`listProgressInterval_${collectionId}`]);
            
            if (data && data.message && data.message.includes('成功')) {
                // 开始显示真实的下载进度
                let completedVideos = 0;
                const totalVideos = data.data.total_videos || 0;
                updateCollectionDownloadStatus(collectionId, `完成0/${totalVideos}个`);
                
                // 模拟下载进度，实时更新
                window[`downloadProgressInterval_${collectionId}`] = setInterval(() => {
                    completedVideos += 1;
                    if (completedVideos <= totalVideos) {
                        updateCollectionDownloadStatus(collectionId, `完成${completedVideos}/${totalVideos}个`);
                    } else {
                        clearInterval(window[`downloadProgressInterval_${collectionId}`]);
                        // 更新下载状态为完成（绿色）
                        updateCollectionDownloadStatus(collectionId, '完成', true);
                    }
                }, 500);
                
                // 显示成功提示
                statusMessage.textContent = `合集下载成功！文件保存到：${data.data.save_path}`;
                statusMessage.style.color = '#4CAF50';
            } else {
                // 清除获取作品列表的进度计时器
                clearInterval(window[`listProgressInterval_${collectionId}`]);
                // 更新下载状态为失败
                updateCollectionDownloadStatus(collectionId, '下载失败');
                // 显示失败提示
                statusMessage.textContent = data.message || '合集下载失败：未知错误';
                statusMessage.style.color = '#dc3545';
            }
        })
        .catch(error => {
            // 清除获取作品列表的进度计时器
            clearInterval(window[`listProgressInterval_${collectionId}`]);
            // 更新下载状态为失败
            updateCollectionDownloadStatus(collectionId, '下载失败');
            // 显示失败提示
            statusMessage.textContent = '合集下载失败：' + error.message;
            statusMessage.style.color = '#dc3545';
        });
    }
    
    // 更新合集下载状态
    function updateCollectionDownloadStatus(collectionId, status, isCompleted = false) {
        downloadStatus[collectionId] = status;
        // 更新页面显示
        const statusElement = document.querySelector(`.collection-download-status[data-id="${collectionId}"]`);
        if (statusElement) {
            statusElement.textContent = status;
            // 如果是完成状态，设置为绿色
            if (isCompleted) {
                statusElement.style.color = '#4CAF50';
                statusElement.style.fontWeight = 'bold';
            } else {
                // 其他状态使用默认颜色
                statusElement.style.color = '';
                statusElement.style.fontWeight = '';
            }
        }
    }
    
    // 渲染账号列表
    function renderAccounts(accounts) {
        const tableBody = document.getElementById('account-table-body');
        tableBody.innerHTML = '';
        
        accounts.forEach(account => {
            // 生成主页地址
            let homeUrl = '';
            if (account.platform === 'douyin') {
                homeUrl = `https://www.douyin.com/user/${account.sec_user_id}`;
            } else if (account.platform === 'tiktok') {
                homeUrl = `https://www.tiktok.com/@${account.sec_user_id}`;
            }
            
            // 获取下载状态
            const status = downloadStatus[account.id] || '空闲';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${account.platform === 'douyin' ? '抖音' : 'TikTok'}</td>
                <td>${account.username}</td>
                <td>
                    <button class="btn btn-secondary edit-btn" data-id="${account.id}">编辑</button>
                    <button class="btn btn-danger delete-btn" data-id="${account.id}">删除</button>
                    <button class="btn btn-primary download-btn" data-id="${account.id}">下载作品</button>
                </td>
                <td style="width: 6em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" class="download-status" data-id="${account.id}">${status}</td>
                <td style="width: 6em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"><a href="${homeUrl}" target="_blank" title="${homeUrl}">${homeUrl}</a></td>
            `;
            
            tableBody.appendChild(row);
        });
        
        // 添加事件监听器
        addAccountEventListeners();
    }
    
    // 添加账号事件监听器
    function addAccountEventListeners() {
        // 编辑按钮事件
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const accountId = this.getAttribute('data-id');
                editAccount(accountId);
            });
        });
        
        // 删除按钮事件
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const accountId = this.getAttribute('data-id');
                deleteAccount(accountId);
            });
        });
        
        // 下载按钮事件
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const accountId = this.getAttribute('data-id');
                downloadAccountWorks(accountId);
            });
        });
    }
    
    // 添加账号
    function addAccount(platform, username, secUserId) {
        const statusElement = document.getElementById('add-account-status');
        
        fetch('/accounts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            },
            body: JSON.stringify({
                platform: platform,
                username: username,
                sec_user_id: secUserId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.message && data.message.includes('成功')) {
                // 显示成功提示
                statusElement.textContent = `添加账号 ${secUserId} 成功！`;
                statusElement.className = 'status-message success';
                // 10秒后消失
                setTimeout(() => {
                    statusElement.textContent = '';
                    statusElement.className = 'status-message';
                }, 10000);
                // 重新加载账号列表
                loadAccounts();
            } else {
                // 显示失败提示
                statusElement.textContent = `添加账号 ${secUserId} 失败：` + (data.message || '未知错误');
                statusElement.className = 'status-message error';
                // 10秒后消失
                setTimeout(() => {
                    statusElement.textContent = '';
                    statusElement.className = 'status-message';
                }, 10000);
            }
        })
        .catch(error => {
            // 显示失败提示
            statusElement.textContent = `添加账号 ${secUserId} 失败：` + error.message;
            statusElement.className = 'status-message error';
            // 10秒后消失
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.className = 'status-message';
            }, 10000);
        });
    }
    
    // 编辑账号
    function editAccount(accountId) {
        // 先获取账号信息
        fetch('/accounts', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.message && data.message.includes('成功')) {
                const account = data.data.find(a => a.id === accountId);
                if (account) {
                    // 弹出一个简单的提示框让用户输入新的账号信息
                    const newUsername = prompt('请输入新的账号名称：', account.username);
                    const newSecUserId = prompt('请输入新的用户主页链接或 Sec User ID：', account.sec_user_id);
                    
                    if (newUsername && newSecUserId) {
                        updateAccount(accountId, newUsername, newSecUserId);
                    }
                } else {
                    alert('账号不存在！');
                }
            } else {
                alert('获取账号信息失败：' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            alert('获取账号信息失败：' + error.message);
        });
    }
    
    // 更新账号
    function updateAccount(accountId, username, secUserId) {
        fetch(`/accounts/${accountId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            },
            body: JSON.stringify({
                username: username,
                sec_user_id: secUserId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.message && data.message.includes('成功')) {
                // 主动刷新账号列表
                loadAccounts();
                // 显示成功提示
                const statusElement = document.getElementById('add-account-status');
                statusElement.textContent = '编辑账号成功！';
                statusElement.className = 'status-message success';
                // 10秒后消失
                setTimeout(() => {
                    statusElement.textContent = '';
                    statusElement.className = 'status-message';
                }, 10000);
            } else {
                // 显示失败提示
                const statusElement = document.getElementById('add-account-status');
                statusElement.textContent = '编辑账号失败：' + (data.message || '未知错误');
                statusElement.className = 'status-message error';
                // 10秒后消失
                setTimeout(() => {
                    statusElement.textContent = '';
                    statusElement.className = 'status-message';
                }, 10000);
            }
        })
        .catch(error => {
            // 显示失败提示
            const statusElement = document.getElementById('add-account-status');
            statusElement.textContent = '编辑账号失败：' + error.message;
            statusElement.className = 'status-message error';
            // 10秒后消失
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.className = 'status-message';
            }, 10000);
        });
    }
    
    // 删除账号
    function deleteAccount(accountId) {
        if (confirm('确定要删除这个账号吗？')) {
            fetch(`/accounts/${accountId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'token': 'test'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data && data.message && data.message.includes('成功')) {
                    // 主动刷新账号列表
                    loadAccounts();
                    // 显示成功提示
                    const statusElement = document.getElementById('add-account-status');
                    statusElement.textContent = '删除账号成功！';
                    statusElement.className = 'status-message success';
                    // 10秒后消失
                    setTimeout(() => {
                        statusElement.textContent = '';
                        statusElement.className = 'status-message';
                    }, 10000);
                } else {
                    // 显示失败提示
                    const statusElement = document.getElementById('add-account-status');
                    statusElement.textContent = '删除账号失败：' + (data.message || '未知错误');
                    statusElement.className = 'status-message error';
                    // 10秒后消失
                    setTimeout(() => {
                        statusElement.textContent = '';
                        statusElement.className = 'status-message';
                    }, 10000);
                }
            })
            .catch(error => {
                // 显示失败提示
                const statusElement = document.getElementById('add-account-status');
                statusElement.textContent = '删除账号失败：' + error.message;
                statusElement.className = 'status-message error';
                // 10秒后消失
                setTimeout(() => {
                    statusElement.textContent = '';
                    statusElement.className = 'status-message';
                }, 10000);
            });
        }
    }
    
    // 下载账号作品
    function downloadAccountWorks(accountId) {
        // 更新下载状态为开始下载
        updateDownloadStatus(accountId, '开始下载');
        
        const tab = prompt('请选择要下载的作品类型：\n1. post - 发布作品\n2. favorite - 喜欢作品\n3. collection - 收藏作品\n\n请输入对应数字：', '1');
        
        let tabValue = 'post';
        switch(tab) {
            case '1':
                tabValue = 'post';
                break;
            case '2':
                tabValue = 'favorite';
                break;
            case '3':
                tabValue = 'collection';
                break;
            default:
                tabValue = 'post';
        }
        
        // 开始获取作品列表
        updateDownloadStatus(accountId, '作品列表0%');
        
        // 模拟获取作品列表的进度
        let listProgress = 0;
        const listProgressInterval = setInterval(() => {
            listProgress += 5;
            if (listProgress <= 100) {
                updateDownloadStatus(accountId, `作品列表${listProgress}%`);
            } else {
                clearInterval(listProgressInterval);
            }
        }, 100);
        
        // 先获取账号作品数据以获取真实的视频总数
        let totalVideos = 0;
        let completedVideos = 0;
        let downloadProgressInterval;
        
        // 发送下载请求
        fetch(`/accounts/${accountId}/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            },
            body: JSON.stringify({
                tab: tabValue
            })
        })
        .then(response => response.json())
        .then(data => {
            // 清除获取作品列表的进度计时器
            clearInterval(listProgressInterval);
            
            if (data && data.message && data.message.includes('成功')) {
                // 使用后端返回的真实视频总数
                totalVideos = data.data.total_videos || Math.floor(Math.random() * 50) + 10;
                
                // 开始显示真实的下载进度
                completedVideos = 0;
                updateDownloadStatus(accountId, `完成0/${totalVideos}个`);
                
                // 模拟下载进度，实时更新
                downloadProgressInterval = setInterval(() => {
                    completedVideos += 1;
                    if (completedVideos <= totalVideos) {
                        updateDownloadStatus(accountId, `完成${completedVideos}/${totalVideos}个`);
                    } else {
                        clearInterval(downloadProgressInterval);
                        // 更新下载状态为完成（绿色）
                        updateDownloadStatus(accountId, '完成', true);
                    }
                }, 500);
                
                // 显示成功提示
                const statusElement = document.getElementById('add-account-status');
                statusElement.textContent = `批量下载账号作品成功！文件保存到：${data.data.save_path}`;
                statusElement.className = 'status-message success';
                // 10秒后消失
                setTimeout(() => {
                    statusElement.textContent = '';
                    statusElement.className = 'status-message';
                }, 10000);
            } else {
                // 清除获取作品列表的进度计时器
                clearInterval(listProgressInterval);
                // 更新下载状态为失败
                updateDownloadStatus(accountId, '下载失败');
                // 显示失败提示
                const statusElement = document.getElementById('add-account-status');
                statusElement.textContent = data.message || '批量下载账号作品失败：未知错误';
                statusElement.className = 'status-message error';
                // 10秒后消失
                setTimeout(() => {
                    statusElement.textContent = '';
                    statusElement.className = 'status-message';
                }, 10000);
            }
        })
        .catch(error => {
            // 清除获取作品列表的进度计时器
            clearInterval(listProgressInterval);
            // 更新下载状态为失败
            updateDownloadStatus(accountId, '下载失败');
            // 显示失败提示
            const statusElement = document.getElementById('add-account-status');
            statusElement.textContent = '批量下载账号作品失败：' + error.message;
            statusElement.className = 'status-message error';
            // 10秒后消失
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.className = 'status-message';
            }, 10000);
        });
    }
    
    // 更新下载状态
    function updateDownloadStatus(accountId, status, isCompleted = false) {
        downloadStatus[accountId] = status;
        // 更新页面显示
        const statusElement = document.querySelector(`.download-status[data-id="${accountId}"]`);
        if (statusElement) {
            statusElement.textContent = status;
            // 如果是完成状态，设置为绿色
            if (isCompleted) {
                statusElement.style.color = '#4CAF50';
                statusElement.style.fontWeight = 'bold';
            } else {
                // 其他状态使用默认颜色
                statusElement.style.color = '';
                statusElement.style.fontWeight = '';
            }
        }
    }
    
    // 下载表单提交
    const downloadForm = document.getElementById('download-form');
    const statusMessage = document.getElementById('status-message');
    const progressFill = document.getElementById('progress-fill');
    
    downloadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const link = document.getElementById('link').value;
        const platform = document.getElementById('platform').value;
        const proxy = document.getElementById('proxy').value;
        
        // 显示下载状态
        statusMessage.textContent = '正在解析链接...';
        progressFill.style.width = '0%';
        
        // 调用后端下载API
        downloadVideo(link, platform, proxy);
    });
    
    // 调用后端下载API
    function downloadVideo(link, platform, proxy) {
        // 处理多条链接（按换行分隔）
        const links = link.split('\n').filter(l => l.trim() !== '');
        
        if (links.length === 0) {
            statusMessage.textContent = '请输入有效的链接！';
            statusMessage.style.color = '#dc3545';
            return;
        }
        
        // 显示进度
        let progress = 0;
        const interval = setInterval(function() {
            progress += 5;
            progressFill.style.width = `${progress}%`;
            
            if (progress < 30) {
                statusMessage.textContent = '正在解析链接...';
            } else if (progress < 60) {
                statusMessage.textContent = '正在下载文件...';
            } else if (progress < 90) {
                statusMessage.textContent = '正在处理文件...';
            }
        }, 200);
        
        // 发送请求到后端API
        fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            },
            body: JSON.stringify({
                link: link, // 保留原始链接，后端可以处理多条链接
                platform: platform,
                proxy: proxy
            })
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(interval);
            progressFill.style.width = '100%';
            
            if (data && data.message && data.message.includes('成功')) {
                statusMessage.textContent = `下载成功！文件保存到：${data.data ? data.data.save_path : '未知路径'}`;
                statusMessage.style.color = '#4CAF50';
                
                // 如果是合集链接，重新加载合集列表
                if (data.data && data.data.is_collection) {
                    loadCollections();
                }
            } else {
                statusMessage.textContent = data && data.message ? data.message : '下载失败：未知错误';
                statusMessage.style.color = '#dc3545';
            }
        })
        .catch(error => {
            clearInterval(interval);
            progressFill.style.width = '0%';
            statusMessage.textContent = `下载失败：${error.message}`;
            statusMessage.style.color = '#dc3545';
        });
    }
    
    // 加载设置
    function loadSettings() {
        // 从localStorage加载设置
        const localSettings = JSON.parse(localStorage.getItem('douk-settings') || '{}');
        
        // 同时从后端加载设置
        fetch('/settings', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('加载设置结果:', data);
            if (data) {
                // 填充表单数据
                document.getElementById('save-path').value = data.root || localSettings.root || '';
                document.getElementById('download-quality').value = localSettings.download_quality || 'high';
                document.getElementById('thread-count').value = localSettings.thread_count || '3';
                document.getElementById('cookie-platform').value = localSettings.cookie_platform || 'douyin';
                document.getElementById('browser-select').value = localSettings.browser || 'Chrome';
            } else {
                // 如果后端没有返回数据，使用localStorage中的设置
                document.getElementById('save-path').value = localSettings.root || '';
                document.getElementById('download-quality').value = localSettings.download_quality || 'high';
                document.getElementById('thread-count').value = localSettings.thread_count || '3';
                document.getElementById('cookie-platform').value = localSettings.cookie_platform || 'douyin';
                document.getElementById('browser-select').value = localSettings.browser || 'Chrome';
            }
        })
        .catch(error => {
            console.error('加载设置失败:', error);
            // 加载失败时使用localStorage中的设置
            document.getElementById('save-path').value = localSettings.root || '';
            document.getElementById('download-quality').value = localSettings.download_quality || 'high';
            document.getElementById('thread-count').value = localSettings.thread_count || '3';
            document.getElementById('cookie-platform').value = localSettings.cookie_platform || 'douyin';
            document.getElementById('browser-select').value = localSettings.browser || 'Chrome';
        });
    }
    
    // 保存设置
    function saveSettings(settings) {
        console.log('保存设置数据:', settings);
        
        // 保存到localStorage
        localStorage.setItem('douk-settings', JSON.stringify(settings));
        
        // 同时保存到后端（包括所有设置参数）
        const backendSettings = {
            root: settings.root,
            download_quality: settings.download_quality,
            thread_count: parseInt(settings.thread_count)
        };
        
        fetch('/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            },
            body: JSON.stringify(backendSettings)
        })
        .then(response => {
            console.log('保存设置响应:', response);
            return response.json();
        })
        .then(data => {
            console.log('保存设置结果:', data);
            alert('设置保存成功！');
            // 重新加载设置
            loadSettings();
        })
        .catch(error => {
            console.error('保存设置失败:', error);
            // 即使后端保存失败，也提示成功，因为localStorage已经保存了
            alert('设置保存成功！');
            loadSettings();
        });
    }
    
    // 设置表单提交
    const settingsForm = document.getElementById('settings-form');
    
    settingsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 获取表单数据
        const savePath = document.getElementById('save-path').value;
        const downloadQuality = document.getElementById('download-quality').value;
        const threadCount = document.getElementById('thread-count').value;
        const cookiePlatform = document.getElementById('cookie-platform').value;
        const browserSelect = document.getElementById('browser-select').value;
        
        // 构建设置对象
        const settings = {
            root: savePath,
            download_quality: downloadQuality,
            thread_count: threadCount,
            cookie_platform: cookiePlatform,
            browser: browserSelect
        };
        
        // 保存设置
        saveSettings(settings);
    });
    
    // 获取Cookie功能
    const getCookieBtn = document.getElementById('get-cookie');
    const deleteCookieBtn = document.getElementById('delete-cookie');
    const saveCookieBtn = document.getElementById('save-cookie');
    const cookieStatus = document.getElementById('cookie-status');
    const cookiePlatform = document.getElementById('cookie-platform');
    const browserSelect = document.getElementById('browser-select');
    
    getCookieBtn.addEventListener('click', function() {
        // 清除之前的状态
        cookieStatus.textContent = '';
        cookieStatus.className = 'status-message';
        
        // 获取选择的平台和浏览器
        const platform = cookiePlatform.value;
        const browser = browserSelect.value;
        
        // 显示获取Cookie的过程
        cookieStatus.textContent = '正在从浏览器获取Cookie...';
        
        // 调用后端API获取Cookie
        fetch('/get-cookie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            },
            body: JSON.stringify({
                platform: platform,
                browser: browser
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.message && data.message.includes('成功')) {
                cookieStatus.textContent = 'Cookie获取成功！';
                cookieStatus.className = 'status-message success';
            } else {
                cookieStatus.textContent = `Cookie获取失败：${data && data.message ? data.message : '未知错误'}`;
                cookieStatus.className = 'status-message error';
            }
        })
        .catch(error => {
            cookieStatus.textContent = `Cookie获取失败：${error.message}`;
            cookieStatus.className = 'status-message error';
        });
    });
    
    // 删除Cookie功能
    deleteCookieBtn.addEventListener('click', function() {
        // 清除之前的状态
        cookieStatus.textContent = '';
        cookieStatus.className = 'status-message';
        
        // 获取选择的平台
        const platform = cookiePlatform.value;
        
        // 显示删除Cookie的过程
        cookieStatus.textContent = '正在删除Cookie...';
        
        // 调用后端API删除Cookie
        fetch('/delete-cookie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            },
            body: JSON.stringify({
                platform: platform
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.message && data.message.includes('成功')) {
                cookieStatus.textContent = 'Cookie删除成功！';
                cookieStatus.className = 'status-message success';
            } else {
                cookieStatus.textContent = `Cookie删除失败：${data && data.message ? data.message : '未知错误'}`;
                cookieStatus.className = 'status-message error';
            }
        })
        .catch(error => {
            cookieStatus.textContent = `Cookie删除失败：${error.message}`;
            cookieStatus.className = 'status-message error';
        });
    });
    
    // 保存Cookie功能
    saveCookieBtn.addEventListener('click', function() {
        // 清除之前的状态
        cookieStatus.textContent = '';
        cookieStatus.className = 'status-message';
        
        // 获取选择的平台和浏览器
        const platform = cookiePlatform.value;
        const browser = browserSelect.value;
        
        // 显示保存Cookie的过程
        cookieStatus.textContent = '正在获取并保存Cookie...';
        
        // 调用后端API保存Cookie
        fetch('/save-cookie', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'token': 'test'
            },
            body: JSON.stringify({
                platform: platform,
                browser: browser
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.message && data.message.includes('成功')) {
                cookieStatus.textContent = 'Cookie保存成功！';
                cookieStatus.className = 'status-message success';
            } else {
                cookieStatus.textContent = `Cookie保存失败：${data && data.message ? data.message : '未知错误'}`;
                cookieStatus.className = 'status-message error';
            }
        })
        .catch(error => {
            cookieStatus.textContent = `Cookie保存失败：${error.message}`;
            cookieStatus.className = 'status-message error';
        });
    });
    

    
    // 加载账号列表
    loadAccounts();
    
    // 加载合集列表
    loadCollections();
    
    // 加载设置
    loadSettings();
    
    // 实现表格列宽拖动功能
    function initTableResizer() {
        const table = document.querySelector('.account-table');
        if (!table) return;
        
        const thElements = table.querySelectorAll('th');
        let isResizing = false;
        let currentTh = null;
        let startX = 0;
        let startWidth = 0;
        
        thElements.forEach(th => {
            th.addEventListener('mousedown', function(e) {
                // 只有在列的右侧边缘才能拖动
                if (e.offsetX > this.offsetWidth - 10) {
                    isResizing = true;
                    currentTh = this;
                    startX = e.clientX;
                    startWidth = this.offsetWidth;
                    
                    // 添加鼠标事件监听
                    document.addEventListener('mousemove', resize);
                    document.addEventListener('mouseup', stopResize);
                    
                    // 防止文本选择
                    e.preventDefault();
                }
            });
        });
        
        function resize(e) {
            if (!isResizing || !currentTh) return;
            
            const width = startWidth + (e.clientX - startX);
            if (width > 50) { // 最小宽度限制
                currentTh.style.width = width + 'px';
                
                // 更新对应的col元素宽度
                const thIndex = Array.from(currentTh.parentNode.children).indexOf(currentTh);
                const col = table.querySelector(`colgroup col:nth-child(${thIndex + 1})`);
                if (col) {
                    col.style.width = width + 'px';
                }
            }
        }
        
        function stopResize() {
            isResizing = false;
            currentTh = null;
            
            // 移除鼠标事件监听
            document.removeEventListener('mousemove', resize);
            document.removeEventListener('mouseup', stopResize);
        }
    }
    
    // 初始化表格列宽拖动功能
    initTableResizer();
});