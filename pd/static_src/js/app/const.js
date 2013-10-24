var STATIC_APP_URL = '/static/js/app',
	STATIC_TPL_URL = STATIC_APP_URL+'/tpl';


    var PLACE_TYPES = {
        cemetery: 'По кладбищу',
        area: 'По участку',
        row: 'По ряду',
        cem_year: 'Кладбище + год',
        burial_account_number: 'По рег. номеру захоронения',
        manual: 'Ручное'
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
    };
	// EOF Burial model