// currently bundling various js functions here, need to move to webpack or similar


//==== navmenu behavior ================================================================

$(document).ready(function() {
  attachNavmenuEvents();
  attachTableofContentsEvents();
  attachFootRefEvents();
});

function attachNavmenuEvents() {
  // $('#top-navmenu').toggle(); //debugging toggle
  $('#bottom-navmenu').hide();
  $('#banner .navmenu-button').click((e) => {
    e.preventDefault();
    $('#top-navmenu').toggle();
  });
  $('#page-footer .navmenu-button').click((e) => {
    e.preventDefault();
    $('#bottom-navmenu').toggle();
    $('html, body').scrollTop($('#bottom-navmenu').offset().top);
  });
  $('.navmenu .close').click(e => {
    e.preventDefault();
    $(e.target).closest(".navmenu").parent().toggle();
  });
}

//==== mobile ToC widget ==============================================================

// Event listeners for Table of Contents
function attachTableofContentsEvents() {
  var bodyElement = createBody();
  var dropdownLinks = createDropdownLinks();
  var deviceView = createDeviceView(dropdownLinks, bodyElement);
  deviceView.init();
}

var createDeviceView = function(dropdownLinks, bodyElement) {
  function init() {
    attachStartingEvents();
    attachClosingEvents();
  }

  function attachStartingEvents() {
    dropdownLinks.hide();
    attachToggleDropdownLinksListener();
  }

  function attachToggleDropdownLinksListener() {
    $('.dropdown-button').click((e) => {
      e.preventDefault();
      dropdownLinks.toggle();
      coordinateBodyScroll();
    });
  }

  function coordinateBodyScroll() {
    if (dropdownLinks.areVisible()) {
      bodyElement.disableScroll();
    } else {
      bodyElement.enableScroll();
    }
  }

  function clickOutOfDropdownContentListener() {
    $(document).click((e) => {
      if(!$(e.target).closest('#toc-dropdown').length) {
        if (dropdownLinks.areVisible()) {
          dropdownLinks.hide();
          bodyElement.enableScroll();
        }
      }
    });
  };

  function clickFromLinksDropdownContentListener() {
    $('#dropdownLinks').children().click((e) => {
      dropdownLinks.hide();
      if (!dropdownLinks.areVisible()) {
        bodyElement.enableScroll();
      }
    });
  };

  function attachClosingEvents() {
    clickOutOfDropdownContentListener();
    clickFromLinksDropdownContentListener();
  }

  return {
    init: init
  }
}

var createBody = function() {
  var bodyElement = function() {
    return $('body');
  }
  function disableBodyScroll() {
    bodyElement().toggleClass('no-scroll', true);
  }
  function enableBodyScroll() {
    bodyElement().toggleClass('no-scroll', false);
  }

  return {
    disableScroll: disableBodyScroll,
    enableScroll: enableBodyScroll
  }

}

var createDropdownLinks = function() {
    var dropdownLinks = function () {
      return $('#dropdownLinks');
    };

  function container() {
    return $('#toc-dropdown');
  }


    var dropdownLinksAreVisible = function () {
      return dropdownLinks().is(":visible");
    };

    function hide() {
      container().removeClass('show-dropdown-links');
    }

    function toggle() {
      container().toggleClass('show-dropdown-links');
    }

    return {
      hide: hide,
      toggle: toggle,
      areVisible: dropdownLinksAreVisible
    }
};


//==== support for article cards ================================================================

function isSmallScreen() {
  return window.innerWidth < 600
}


function encloseWhenSmall(mainSelector, summarySelector) {
  if (isSmallScreen())
    document.querySelectorAll(mainSelector).forEach( card => {
      const detailsElement = document.createElement('details');
      card.appendChild(detailsElement);
      const summaryElement = document.createElement('summary');
      detailsElement.appendChild(summaryElement);
      const summary = card.querySelector(summarySelector);
      summaryElement.appendChild(summary);
      detailsElement.appendChild(card.querySelector('.card-body'));
      summary.textContent = summaryElement.querySelector('a').textContent;
    });
}

//==== footnotes ================================================================

function attachFootRefEvents() {
  document.querySelectorAll(".foot-ref")
    .forEach(element => element.addEventListener('click', event => clickFootRef(event, element)))
}

function clickFootRef(event, anElement) {
  const footnotes = document.querySelectorAll("." + anElement.getAttribute('data-footnote'));
  footnotes.forEach(e => e.classList.toggle('visible'));
}

//==== Carousel ================================================================
class Carousel {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.pages = this.container.getAttribute('data-pages').split(' ');
    this.currentPage = null
    this.init();
  }

  init() {
    this.showPage(this.pages[0]);
    this.addEventListeners();
  }

  prevPage() {
    this.showPage(this.pages[Math.max(this.currentIndex - 1, 0)])
   }

  nextPage() {
    this.showPage(this.pages[Math.min(this.currentIndex + 1, this.pages.length -1)])
  }

  hidePage(fadingClass, newClass) {
    if (!fadingClass) return;
    this.container.querySelectorAll('.btn-page.' + this.currentPage)
      .forEach( i => this.hideElement(i));
    this.container.querySelectorAll('.content .' + this.currentPage)
      .forEach( i => {
        if (! i.classList.contains(newClass)) this.hideElement(i)
      })
  }
  showPage(pageClass) {
    this.hidePage(this.currentPage, pageClass);
    this.container.querySelectorAll('.btn-page.' + pageClass)
      .forEach(i => this.showElement(i));
    this.container.querySelectorAll('.content .' + pageClass)
      .forEach( i => this.showElement(i));
    this.container.querySelectorAll('.content .progress')
      .forEach( i => this.progress(i, this.currentPage, pageClass))
    this.currentPage = pageClass
  }

  showElement(element) {
    element.classList.add('fading')
    setTimeout(() => {
      element.classList.add('active');
    }, 20);
  }

  hideElement(element) {
    element.classList.remove('active');
    element.addEventListener('transitionend', () => {
      element.classList.remove('fading');
    }, {once: true});
  }

  progress(element, fadingClass, newClass) {
    if (newClass == fadingClass) return;
    element.classList.add('pg-' + newClass);
    element.classList.remove('pg-' + fadingClass);
  }
  get currentIndex() {
    return this.pages.findIndex((it) => it === this.currentPage)
  }

  addEventListeners() {
    const pageButtons = this.container.querySelectorAll('.btn-page');
    const prevButton = this.container.querySelector('.btn-prev');
    const nextButton = this.container.querySelector('.btn-next');

    pageButtons.forEach((button) => {
      button.addEventListener('click', () => this.showPage(button.getAttribute('data-page')));
    });

    prevButton.addEventListener('click', () => this.prevPage());
    nextButton.addEventListener('click', () => this.nextPage());
  }
}



