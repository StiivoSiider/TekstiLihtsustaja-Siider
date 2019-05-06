window.addEventListener('load', function(){
	var nupp = document.getElementById("lihtsustaNupp")
	var laadija = document.getElementById("laadija")
	var tekst = document.getElementById("tekst")
	nupp.addEventListener("click", function(tab){
		tekst.style.display = "none";
		nupp.style.display = "none";
		laadija.style.display  = "block";
		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
			chrome.tabs.sendMessage(tabs[0].id, {action: "tagastaTekst"}, function(response) {
				if (response != null){
					fetch('http://prog.keeleressursid.ee/ss_syntax/?l='+response.tekst)
					  .then(function(response) {
						return response.text();
					  })
					  .then(function(result) {
						  result = result.split("---- ")
						  var info = result[0]
						  var lihtsustatud = result[1].replace("</pre>", "")
						  console.log(lihtsustatud)
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