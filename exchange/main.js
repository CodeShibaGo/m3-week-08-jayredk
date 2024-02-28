(() => {
  const API_ENDPOINT = 'https://api.exchangerate-api.com/v4/latest';

  const primarySelect = document.querySelector('#primary-currency-type');
  const secondarySelect = document.querySelector('#secondary-currency-type');
  const primaryField = document.querySelector('#primary-currency-field');
  const secondaryField = document.querySelector('#secondary-currency-field');

  let rate = [];

  async function getRate(rateType = 'TWD') {
    const api = `${API_ENDPOINT}/${rateType}`;

    rate = await fetch(api)
            .then((res) => res.json());
  }

  function renderSelectOptions(ratesObj) {
    const rates = Object.keys(ratesObj);

    let str = ''
    rates.forEach((rateType) => {
      str += `<option value="${rateType}">${rateType}</option>`
    })

    primarySelect.innerHTML = str;
    secondarySelect.innerHTML = str;
    secondarySelect.value = 'USD' // 預設為美金
  }

  async function calculateValue(isApiCall = true) {
    if (isApiCall) {
      await getRate(primarySelect.value);
    }

    const convertType = secondarySelect.value;
    secondaryField.value = rate.rates[convertType] * primaryField.value;
    renderCurrentRate(convertType);
  }

  function renderCurrentRate(convertType) {
    const currentRate = document.querySelector('#current-rate');
    currentRate.textContent = `1 ${primarySelect.value} = ${rate.rates[convertType]} ${secondarySelect.value}`
  }

  function onPrimaryGroupChange() {
    const primaryGroup = document.querySelector('#primary-group');

    primaryGroup.addEventListener('input', async (e) => {
      const { target } = e;

      if (target.nodeName === 'SELECT') {
        calculateValue();
      } else {
        calculateValue(false);
      }
    })
  }

  function onSecondarySelectChange() {
    secondarySelect.addEventListener('change', () => {
      calculateValue(false);
    });
  }

  function onSwapRateType() {
    const swapBtn = document.querySelector('#swapBtn');

    swapBtn.addEventListener('click', async () => {
      let temp = primarySelect.value;
      primarySelect.value = secondarySelect.value;
      secondarySelect.value = temp;
      calculateValue();
    })
  }

  function bindEvent() {
    onSwapRateType();
    onPrimaryGroupChange();
    onSecondarySelectChange();
  }

  async function init() {
    await getRate();
    renderSelectOptions(rate.rates);
    const convertType = secondarySelect.value;
    renderCurrentRate(convertType);
    bindEvent();
  }

  init();
})()