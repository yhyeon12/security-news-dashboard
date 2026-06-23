fetch("./data/news.json")
  .then(response => response.json())
  .then(data => {
    const container = document.getElementById("newsContainer");

    data.forEach(news => {
      container.innerHTML += `
        <div class="card">
          <span class="tag">${news.category}</span>
          <h2>${news.title}</h2>
          <p>${news.summary}</p>
          <a href="${news.link}" target="_blank">기사 보기</a>
        </div>
      `;
    });
  });