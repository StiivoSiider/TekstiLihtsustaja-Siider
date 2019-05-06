// Peamine eesrakendus tööklass, mis lisab hüpikaknas olevale nupule kuulaja

window.addEventListener('load', function(){
	
	// Hüpikakna kolm elementi
	var nupp = document.getElementById("lihtsustaNupp")
	var laadija = document.getElementById("laadija")
	var tekst = document.getElementById("tekst")
	
	// Kuulaja lisamine
	nupp.addEventListener("click", function(tab){
		// Laadimisanimatsiooni kuvamine, teiste elementide peitmine
		tekst.style.display = "none";
		nupp.style.display = "none";
		laadija.style.display  = "block";
		
		// Saadab sõnumi aktiivsele aknale, mis tagastab markeeritud teksti
		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
			chrome.tabs.sendMessage(tabs[0].id, {action: "tagastaTekst"}, function(response) {
				if (response != null){
					// päring APIle
					fetch('http://prog.keeleressursid.ee/ss_syntax/?l='+response.tekst)
					  .then(function(response) {
						return response.text();
					  })
					  .then(function(result) {
						  result = result.split("---- ")
						  var info = result[0]
						  var lihtsustatud = result[1].replace("</pre>", "")
						  console.log(lihtsustatud)
						  // Lihtsustatud teksti kuvamine
						  if(info.includes("__LIHTSUSTATUD__")){
							tekst.innerHTML = lihtsustatud
							tekst.style.width = "500px";
						  } else {
							tekst.innerHTML = "Teksti ei lihtsustatud!"
							tekst.style.width = "140px";
						  }
					      laadija.style.display  = "none";
						  nupp.style.display = "block";
						  tekst.style.display = "block";
					  });
				} else {
					laadija.style.display  = "none";
					nupp.style.display = "block";
				}
			});
		});
	});
});