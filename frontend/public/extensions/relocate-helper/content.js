// Content script for extracting property and relocation data from websites

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === "extractPropertyData") {
    const propertyData = extractPropertyData();
    sendResponse({data: propertyData});
  }
});

function extractPropertyData() {
  const url = window.location.href;
  let data = {
    source: 'unknown',
    title: document.title,
    url: url
  };

  // Rightmove.co.uk extraction
  if (url.includes('rightmove.co.uk')) {
    data.source = 'rightmove';
    data.price = extractText('.propertyHeaderPrice .price, ._1gfnqJ3Vtd1z40MlC0MzXu');
    data.address = extractText('.property-address, ._2uQQ3SV0eMHL1P6t5ZDo2q');
    data.bedrooms = extractText('.propertyFeatures .bullet, ._1fcftXUEbWfJQOby9N5Crown');
    data.propertyType = extractText('.propertySubType, ._3ZROwvGNl8TCnGaOW1QeBi');
  }
  
  // Zoopla.co.uk extraction
  else if (url.includes('zoopla.co.uk')) {
    data.source = 'zoopla';
    data.price = extractText('.pricing-big, .c-hhzDOE');
    data.address = extractText('.listing-details-address, .c-bVxCCC');
    data.bedrooms = extractText('.listing-details-spec, .c-GUjcD');
    data.propertyType = extractText('.listing-details-property-type, .c-eCUyRs');
  }
  
  // Numbeo.com extraction (cost of living)
  else if (url.includes('numbeo.com')) {
    data.source = 'numbeo';
    data.costOfLivingIndex = extractText('.table_index_cost_of_living_index');
    data.rentIndex = extractText('.table_index_rent_index');
    data.localPurchasingPower = extractText('.table_index_local_purchasing_power_index');
  }

  return data;
}

function extractText(selector) {
  const element = document.querySelector(selector);
  return element ? element.textContent.trim() : null;
}

// Add visual indicator when data is extracted
function showExtractionIndicator() {
  const indicator = document.createElement('div');
  indicator.innerHTML = '🏔️ Relocate Me: Data extracted!';
  indicator.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: #10b981;
    color: white;
    padding: 10px 15px;
    border-radius: 5px;
    z-index: 10000;
    font-family: Arial, sans-serif;
    font-size: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  `;
  document.body.appendChild(indicator);
  setTimeout(() => indicator.remove(), 3000);
}

// Auto-highlight property prices and important information
function highlightImportantInfo() {
  const priceSelectors = [
    '.propertyHeaderPrice',
    '.pricing-big',
    '.price',
    '.c-hhzDOE'
  ];
  
  priceSelectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      if (el && !el.classList.contains('relocate-highlighted')) {
        el.style.cssText += `
          border: 2px solid #10b981 !important;
          background: rgba(16, 185, 129, 0.1) !important;
          border-radius: 4px !important;
        `;
        el.classList.add('relocate-highlighted');
      }
    });
  });
}

// Run highlighting when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', highlightImportantInfo);
} else {
  highlightImportantInfo();
}

// Re-run highlighting when page content changes (SPA navigation)
const observer = new MutationObserver(highlightImportantInfo);
observer.observe(document.body, { childList: true, subtree: true });