var STATIC_APP_URL = '/static/js/app',
	STATIC_TPL_URL = STATIC_APP_URL+'/tpl';


    var PLACE_TYPES = {
        //cemetery: 'По кладбищу',
        area: 'По участку',
        row: 'По ряду',
        cem_year: 'Кладбище + год',
        // cem_year: gettext('Кладбище + год'),
        burial_account_number: 'По рег. номеру захоронения',
        manual: 'Вручную'
   },
    PLACE_ARCHIVE_TYPES = {
        '-area': 'По порядку в пределах участка (-0001 -0002...)',
        burial_account_number: 'По рег. номеру захоронения',
        manual: 'Вручную'
   },
    AVAILABILITY_CHOICES = {
        open:	'Открыт',
        old_only:'Только подзахоронения',
        closed: 'Закрыт'
    },

	DEFAULT_MESSAGES ={
		no_data: "Данные отсутствуют"
	},

	// Burial model
    STATUS_CHOICES = {
        backed:    'Отозвано',
        declined:    'Отклонено',
        draft:    'Черновик',
        ready:    'На согласовании',
        approved:    'Согласовано',
        closed:    'Закрыто',
        exhumated:    'Эксгумировано'
    },

    BURIAL_TYPES = {
        common:    'Новое захоронение',
        additional:'Подзахоронение',
        overlap:   'Захоронение в существующую'
    },

    SOURCE_TYPES = {
        full:    'Электронное',
        ugh:    'Ручное',
        archive:    'Архивное',
        transferred:    'Перенесенное'
    },

    BURIAL_CONTAINERS = {
        container_coffin: 'Гроб',
        container_urn:    'Урна',
        container_ash:    'Прах',
        container_bio:    'Биоотходы'
    },

    STATUS_CHOICES = {
            backed: "Отозвано",
            declined: "Отклонено",
            draft: "Черновик",
            ready: "На согласовании",
            inspecting: "На обследовании",
            approved: "Согласовано",
            closed: "",
            exhumated: "Эксгумировано"
    };

	// EOF Burial model



    
    PHONE_TYPE_MOBILE = 0,
    PHONE_TYPE_CITY = 1,
    PHONE_TYPE_FAX = 2,

    PHONETYPE_CHOICES = [
        {id:0, name:'Мобильный'},
        {id:1, name:'Городской'},
        {id:2, name:'Факс'}
    ],
    
    RESPONCIBLE_CT = 20,

    BURIAL_STATUS_EXHUMATED = 'exhumated',
    
    
    TRANSLATIONS = {
      '__ALL__':'',
      'places_count':'Количество могил в месте',
      'Grave':'Могила',
      'Country':'Страна'
    };
    
window.ngGrid.i18n['en'] = {
	    ngAggregateLabel: 'элементы',
	    ngGroupPanelDescription: 'Для группировки по колонке перетащите сюда ее заголовок',
	    ngSearchPlaceHolder: 'Поиск...',
	    ngMenuText: 'Выберите колонку:',
	    ngShowingItemsLabel: 'Показываемые элементы:',
	    ngTotalItemsLabel: 'Всего элементов:',
	    ngSelectedItemsLabel: 'Выбранные элементы:',
	    ngPageSizeLabel: 'Размер страницы:',
	    ngPagerFirstTitle: 'Первая страница',
	    ngPagerNextTitle: 'Следующая страница',
	    ngPagerPrevTitle: 'Предыдущая страница',
	    ngPagerLastTitle: 'Последняя страница'
	};