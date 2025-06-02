document.addEventListener('DOMContentLoaded', function() {
  const dashboardLink = document.getElementById('dashboard-link');
  const comparisonLink = document.getElementById('comparison-link');
  const housingLink = document.getElementById('housing-link');
  const bookmarkBtn = document.getElementById('bookmark-page');
  const savePropertyBtn = document.getElementById('save-property');

  // Get the dashboard URL from storage or use default
  chrome.storage.sync.get(['dashboardUrl'], function(result) {
    const dashboardUrl = result.dashboardUrl || 'https://your-domain.com/dashboard';
    
    dashboardLink.addEventListener('click', function() {
      chrome.tabs.create({ url: dashboardUrl });
    });
    
    comparisonLink.addEventListener('click', function() {
      chrome.tabs.create({ url: dashboardUrl + '/comparison' });
    });
    
    housingLink.addEventListener('click', function() {
      chrome.tabs.create({ url: dashboardUrl + '/housing' });
    });
  });

  bookmarkBtn.addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      const currentTab = tabs[0];
      chrome.bookmarks.create({
        title: `Relocation Resource: ${currentTab.title}`,
        url: currentTab.url
      }, function(bookmark) {
        showNotification('Page bookmarked successfully!');
      });
    });
  });

  savePropertyBtn.addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: "extractPropertyData"}, function(response) {
        if (response && response.data) {
          // Save property data to storage
          chrome.storage.local.get(['savedProperties'], function(result) {
            const savedProperties = result.savedProperties || [];
            savedProperties.push({
              ...response.data,
              savedAt: new Date().toISOString(),
              url: tabs[0].url
            });
            chrome.storage.local.set({savedProperties: savedProperties}, function() {
              showNotification('Property data saved!');
            });
          });
        } else {
          showNotification('No property data found on this page');
        }
      });
    });
  });

  function showNotification(message) {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      background: #10b981;
      color: white;
      padding: 10px;
      border-radius: 5px;
      z-index: 1000;
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }
});