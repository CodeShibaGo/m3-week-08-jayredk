(() => {
  const API_ENDPOINT = 'https://www.googleapis.com/youtube/v3/search';
  const API_KEY = 'AIzaSyDUQUDfpg_6iA_ycnD5yaAYLSPc495aa8w';
  const videoEmbed = 'https://www.youtube.com/embed';

  const searchForm = document.querySelector('#search');
  const videoList = document.querySelector('#videoList');

  let data = [];


  function getData(api) {
    return fetch(api)
            .then((res) => res.json())
            .then(res => res)
  }

  function renderList(data) {
    let str = '';

    data.items.forEach((videoItem) => {
      const videoInfo = videoItem.snippet;

      str += `<li class="card py-3 bg-light border-0 rounded-0 border-bottom border-dark">
        <div class="row g-0">
          <div class="col-md-4">
            <img src="${videoInfo.thumbnails.high.url}" class="img-fluid rounded" alt="${videoInfo.description}">
          </div>
          <div class="col-md-8">
            <div class="card-body">
              <h3 class="card-title video-title">
                <a data-fancybox class="text-body text-decoration-none" href="${videoEmbed}/${videoItem.id.videoId}">${videoInfo.title}</a>
              </h3>
              <p class="card-text">${videoInfo.description}</p>
              <p class="card-text"><small class="text-body-secondary">By ${videoInfo.channelTitle} on ${convertUTCtoTaipeiTime(videoInfo.publishedAt)}</small></p>
            </div>
          </div>
        </div>
      </li>`;
    })

    videoList.innerHTML = str;
  }

  function onSearch() {
    searchForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const query = e.target[0].value;
      if (query.trim() === '') return;

      const api = `${API_ENDPOINT}?part=snippet,id&type=video&key=${API_KEY}&q=${query}`;
      data = await getData(api);
      renderList(data);
    })
  }

  function convertUTCtoTaipeiTime(utcTimestamp) {
    const utcDate = new Date(utcTimestamp);
    return utcDate.toLocaleString('zh-tw');
  }
  
  function bindEvent() {
    onSearch();
  }

  function init() {
    bindEvent();
    Fancybox.bind('[data-fancybox]');
  }

  init()
})()