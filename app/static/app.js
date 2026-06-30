async function scan() {
  const target = document.getElementById("target").value;
  const results = document.getElementById("results");
  results.innerHTML = "";

  const res = await fetch("/lookup", {
    method:"POST",
    headers:{ "Content-Type":"application/json" },
    body: JSON.stringify({ target })
  });

  const data = await res.json();

  render(data);

  if (data.lat && data.lon) {
    addMarker(
      data.lat,
      data.lon,
      `${data.ip}<br>${data.city}, ${data.country}`
    );
    map.setView([data.lat, data.lon],6);
  }
}

function card(title, value) {
  return `
    <div class="card">
      <div class="card-title">${title}</div>
      <div class="card-value">${value || "N/A"}</div>
    </div>
  `;
}

function render(d) {
  const r = document.getElementById("results");
  r.innerHTML += card("IP Address", d.ip);
  r.innerHTML += card("Country", d.country);
  r.innerHTML += card("Region", d.region);
  r.innerHTML += card("City", d.city);
  r.innerHTML += card("Coordinates", `${d.lat}, ${d.lon}`);
  r.innerHTML += card("ISP", d.isp);
  r.innerHTML += card("Organization", d.org);
  r.innerHTML += card("ASN", d.asn);
}
