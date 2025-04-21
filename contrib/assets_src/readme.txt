Как получить и возможно добавить в pd/assets_src

    - bower
        ubuntu 16.4:
            * скачать NodeJS: http://nodejs.org/
            * распаковать, cd node-<VERSION>; ./configure && make && sudo make install
            * sudo npm install -g bower
        ubuntu 18.4+:
            sudo apt install nodejs
            sudo apt install npm
            sudo npm install -g bower

    * cd ~/projects/pd_web
    * туда положить bower.json
    * bower install
        Там выбрать пункт 1:
            1) angular#1.0.8 which resolved to 1.0.8 and is required by angular-cookies#1.0.8, angular-resource#1.0.8, PD
