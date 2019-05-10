// Loob kuulaja, mis korrektse sõnumi korral tagastab markeeritud teksti
chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    if (request.action == 'tagastaTekst')
		sendResponse({tekst: window.getSelection().toString().trim()});
  });