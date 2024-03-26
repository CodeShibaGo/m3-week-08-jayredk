(() => {
  const API_ENDPOINT = 'https://www.googleapis.com/youtube/v3/search';
  const API_KEY = 'AIzaSyCw0c9PN_cbgdcDh9D-zqzr3n_Bcj2KeRc';
  const videoEmbed = 'https://www.youtube.com/embed';

  const searchForm = document.querySelector('#search');
  const videoList = document.querySelector('#videoList');
  const pagination = document.querySelector('#pagination');

  let data = [];
  let query = '';


  async function getData(api) {
    try {
      const res = await fetch(api);

      if (!res.ok) {
        throw new Error(`Fail fetch data from ${api}: ${res.status} ${res.statusText}`);
      }

      return res.json();

    } catch (error) {
      console.error('Error occurred while fetching data:', error);
      throw error;
    }
  }

  function getApiUrl(query, pageToken = '') {
    return `${API_ENDPOINT}?part=snippet,id&type=video&key=${API_KEY}&q=${query}&pageToken=${pageToken}`;
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

  function renderPagination(prevToken, nextToken) {
    let str = '';

    if (prevToken) {
      str += `<li class="page-item"><a data-page="${prevToken}" class="page-link text-secondary" href="#">
        <span class="material-symbols-outlined fs-6 align-middle">chevron_left</span>
      </a></li>`
    }

    if (nextToken) {
      str += `<li class="page-item"><a data-page="${nextToken}" class="page-link text-secondary" href="#">
          <span class="material-symbols-outlined fs-6 align-middle">chevron_right</span>
        </a></li>`
    }

    pagination.innerHTML = str;
  }

  function onPageChange() {
    pagination.addEventListener('click', async (e) => {
      const targetDom = e.target;
      if (targetDom.nodeName === 'UL') return;

      token = targetDom.closest('a').getAttribute('data-page');

      const api = getApiUrl(query, token);
      data = await getData(api);
      renderList(data);
      const { prevPageToken, nextPageToken } = data;
      renderPagination(prevPageToken, nextPageToken)
    })
  }

  function onSearch() {
    searchForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      query = e.target[0].value.trim();
      if (query === '') return;

      const api = getApiUrl(query);
      data = await getData(api);
      renderList(data);
      const { prevPageToken, nextPageToken } = data;
      renderPagination(prevPageToken, nextPageToken)
    })
  }

  function convertUTCtoTaipeiTime(utcTimestamp) {
    const utcDate = new Date(utcTimestamp);
    return utcDate.toLocaleString('zh-tw');
  }
  
  function bindEvent() {
    onSearch();
    onPageChange()
  }

  function init() {
    bindEvent();
    Fancybox.bind('[data-fancybox]');
  }

  init()
})()
