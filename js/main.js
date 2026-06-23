let newsData = [];

fetch("./data/news.json")
  .then(response => response.json())
  .then(data => {
    newsData = data;
    renderNews(newsData);
  })
  .catch(error => {
    console.error("news.json 로드 실패:", error);
  });

function renderNews(data) {
  const container = document.getElementById("newsContainer");
  container.innerHTML = "";

  if (data.length === 0) {
    container.innerHTML = "<p>표시할 뉴스가 없습니다.</p>";
    return;
  }

  data.forEach(news => {
    container.innerHTML += `
      <div class="card">
        <span class="tag">${news.category}</span>
        <h2>${news.title}</h2>
        <p>${news.summary}</p>
        <p><strong>출처:</strong> ${news.source}</p>
        <a href="${news.url}" target="_blank">기사 보기</a>
      </div>
    `;
  });
}

function filterNews(category) {
  if (category === "전체") {
    renderNews(newsData);
    return;
  }

  const filteredData = newsData.filter(news => news.category === category);
  renderNews(filteredData);
}