# -*- coding: utf-8 -*-
"""
内嵌拼音 fallback 表（无声调，u 表示 u，v 表示 ü 仅在 l/n 后）。

用途：当运行环境没有安装 pypinyin 时，作为应急拼音来源，覆盖日常高频汉字。
完整拼音支持依赖 pypinyin（pip install pypinyin），可覆盖全部汉字（含多音字）。
本表仅保证常用字可用，生僻字/专有名词可能缺失。
"""

CHAR_PINYIN = {
# 代词 / 助词 / 连词 / 介词 / 副词
"的":"de","了":"le","是":"shi","我":"wo","你":"ni","他":"ta","她":"ta","它":"ta",
"们":"men","在":"zai","有":"you","和":"he","与":"yu","及":"ji","而":"er","或":"huo",
"把":"ba","被":"bei","给":"gei","对":"dui","为":"wei","向":"xiang","从":"cong","自":"zi",
"于":"yu","以":"yi","因":"yin","为":"wei","故":"gu","但":"dan","却":"que","也":"ye",
"都":"dou","很":"hen","最":"zui","太":"tai","更":"geng","还":"hai","又":"you","再":"zai",
"不":"bu","没":"mei","无":"wu","未":"wei","别":"bie","莫":"mo","非":"fei","勿":"wu",
"这":"zhe","那":"na","哪":"na","此":"ci","该":"gai","各":"ge","每":"mei","某":"mou",
"个":"ge","些":"xie","种":"zhong","类":"lei","件":"jian","位":"wei","名":"ming","条":"tiao",
"的":"de","地":"de","得":"de","着":"zhe","过":"guo","来":"lai","去":"qu","到":"dao",
"上":"shang","下":"xia","中":"zhong","里":"li","外":"wai","内":"nei","前":"qian","后":"hou",
"左":"zuo","右":"you","东":"dong","西":"xi","南":"nan","北":"bei","间":"jian","旁":"pang",
"会":"hui","能":"neng","可":"ke","应":"ying","该":"gai","要":"yao","想":"xiang","愿":"yuan",
"就":"jiu","才":"cai","已":"yi","将":"jiang","正":"zheng","刚":"gang","常":"chang","总":"zong",
"并":"bing","且":"qie","若":"ruo","如":"ru","若":"ruo","虽":"sui","然":"ran","则":"ze",
"之":"zhi","其":"qi","其":"qi","于":"yu","乎":"hu","与":"yu","及":"ji","乃":"nai","兮":"xi",
# 数词 / 量词 / 时间
"一":"yi","二":"er","三":"san","四":"si","五":"wu","六":"liu","七":"qi","八":"ba","九":"jiu","零":"ling",
"十":"shi","百":"bai","千":"qian","万":"wan","亿":"yi","半":"ban","两":"liang","双":"shuang",
"第":"di","初":"chu","多":"duo","少":"shao","几":"ji","许":"xu","余":"yu","整":"zheng",
"年":"nian","月":"yue","日":"ri","时":"shi","分":"fen","秒":"miao","点":"dian","周":"zhou","天":"tian",
"今":"jin","明":"ming","昨":"zuo","前":"qian","后":"hou","早":"zao","晚":"wan","夜":"ye","春":"chun",
"夏":"xia","秋":"qiu","冬":"dong","季":"ji","晨":"chen","午":"wu","昏":"hun","旦":"dan",
# 常用动词
"说":"shuo","看":"kan","听":"ting","吃":"chi","喝":"he","走":"zou","跑":"pao","飞":"fei","坐":"zuo",
"站":"zhan","睡":"shui","想":"xiang","知":"zhi","道":"dao","学":"xue","教":"jiao","写":"xie","读":"du",
"做":"zuo","干":"gan","工":"gong","作":"zuo","用":"yong","使":"shi","让":"rang","带":"dai","拿":"na",
"放":"fang","开":"kai","关":"guan","进":"jin","出":"chu","回":"hui","过":"guo","送":"song","给":"gei",
"买":"mai","卖":"mai","借":"jie","还":"hai","帮":"bang","请":"qing","问":"wen","答":"da","叫":"jiao",
"打":"da","拉":"la","推":"tui","提":"ti","抓":"zhua","抱":"bao","背":"bei","抬":"tai","举":"ju",
"爱":"ai","恨":"hen","怕":"pa","喜":"xi","怒":"nu","哀":"ai","乐":"le","忧":"you","思":"si",
"记":"ji","忘":"wang","懂":"dong","怕":"pa","信":"xin","疑":"yi","觉":"jue","感":"gan","悟":"wu",
"生":"sheng","死":"si","活":"huo","病":"bing","医":"yi","治":"zhi","养":"yang","护":"hu","救":"jiu",
"种":"zhong","养":"yang","长":"zhang","成":"cheng","变":"bian","改":"gai","造":"zao","建":"jian",
"发":"fa","现":"xian","发":"fa","展":"zhan","研":"yan","究":"jiu","探":"tan","索":"suo","发":"fa",
"取":"qu","得":"de","失":"shi","获":"huo","弃":"qi","留":"liu","弃":"qi","选":"xuan","择":"ze",
# 常用形容词
"大":"da","小":"xiao","高":"gao","低":"di","长":"chang","短":"duan","宽":"kuan","窄":"zhai","厚":"hou",
"薄":"bao","重":"zhong","轻":"qing","快":"kuai","慢":"man","新":"xin","旧":"jiu","好":"hao","坏":"huai",
"美":"mei","丑":"chou","善":"shan","恶":"e","真":"zhen","假":"jia","对":"dui","错":"cuo","正":"zheng",
"反":"fan","同":"tong","异":"yi","多":"duo","少":"shao","全":"quan","半":"ban","满":"man","空":"kong",
"红":"hong","绿":"lv","蓝":"lan","白":"bai","黑":"hei","黄":"huang","青":"qing","紫":"zi","灰":"hui",
"热":"re","冷":"leng","暖":"nuan","凉":"liang","干":"gan","湿":"shi","硬":"ying","软":"ruan","亮":"liang",
"暗":"an","清":"qing","浊":"zhuo","静":"jing","闹":"nao","安":"an","危":"wei","险":"xian","平":"ping",
"甜":"tian","苦":"ku","酸":"suan","辣":"la","咸":"xian","香":"xiang","臭":"chou","鲜":"xian","淡":"dan",
"老":"lao","幼":"you","男":"nan","女":"nv","强":"qiang","弱":"ruo","富":"fu","贫":"pin","贵":"gui",
"贱":"jian","远":"yuan","近":"jin","深":"shen","浅":"qian","圆":"yuan","方":"fang","直":"zhi","弯":"wan",
# 常用名词（人/自然/社会）
"人":"ren","口":"kou","手":"shou","足":"zu","头":"tou","心":"xin","身":"shen","目":"mu","耳":"er",
"鼻":"bi","舌":"she","牙":"ya","血":"xue","骨":"gu","皮":"pi","发":"fa","脸":"lian","眼":"yan",
"爸":"ba","妈":"ma","哥":"ge","姐":"jie","弟":"di","妹":"mei","儿":"er","女":"nv","子":"zi",
"夫":"fu","妻":"qi","父":"fu","母":"mu","爷":"ye","奶":"nai","叔":"shu","舅":"jiu","姑":"gu",
"家":"jia","房":"fang","屋":"wu","门":"men","窗":"chuang","墙":"qiang","桌":"zhuo","椅":"yi","床":"chuang",
"书":"shu","笔":"bi","纸":"zhi","墨":"mo","画":"hua","琴":"qin","棋":"qi","字":"zi","文":"wen",
"水":"shui","火":"huo","土":"tu","石":"shi","山":"shan","河":"he","海":"hai","湖":"hu","江":"jiang",
"风":"feng","雨":"yu","雪":"xue","冰":"bing","雷":"lei","电":"dian","云":"yun","星":"xing","月":"yue",
"日":"ri","光":"guang","影":"ying","声":"sheng","色":"se","气":"qi","味":"wei","香":"xiang","花":"hua",
"草":"cao","树":"shu","木":"mu","林":"lin","叶":"ye","根":"gen","枝":"zhi","果":"guo","米":"mi",
"饭":"fan","菜":"cai","茶":"cha","酒":"jiu","肉":"rou","鱼":"yu","鸡":"ji","蛋":"dan","盐":"yan",
"国":"guo","城":"cheng","村":"cun","镇":"zhen","街":"jie","路":"lu","桥":"qiao","车":"che","船":"chuan",
"机":"ji","电":"dian","灯":"deng","线":"xian","网":"wang","波":"bo","油":"you","药":"yao","金":"jin",
"银":"yin","铜":"tong","铁":"tie","玉":"yu","珠":"zhu","宝":"bao","钱":"qian","币":"bi","市":"shi",
"学":"xue","校":"xiao","师":"shi","生":"sheng","友":"you","朋":"peng","群":"qun","队":"dui","军":"jun",
"官":"guan","兵":"bing","法":"fa","律":"lv","政":"zheng","党":"dang","民":"min","族":"zu","史":"shi",
"世":"shi","界":"jie","时":"shi","代":"dai","事":"shi","业":"ye","功":"gong","名":"ming","利":"li",
"理":"li","智":"zhi","情":"qing","意":"yi","志":"zhi","念":"nian","梦":"meng","想":"xiang","望":"wang",
"言":"yan","语":"yu","话":"hua","音":"yin","歌":"ge","诗":"shi","词":"ci","曲":"qu","调":"diao",
"道":"dao","德":"de","仁":"ren","义":"yi","礼":"li","智":"zhi","信":"xin","勇":"yong","谦":"qian",
# 常用抽象/动作补充
"开":"kai","关":"guan","立":"li","坐":"zuo","卧":"wo","行":"xing","止":"zhi","进":"jin","退":"tui",
"升":"sheng","降":"jiang","转":"zhuan","弯":"wan","直":"zhi","合":"he","分":"fen","离":"li","聚":"ju",
"收":"shou","发":"fa","存":"cun","取":"qu","查":"cha","找":"zhao","看":"kan","望":"wang","观":"guan",
"闻":"wen","尝":"chang","触":"chu","思":"si","考":"kao","虑":"lv","谋":"mou","划":"hua","计":"ji",
"言":"yan","语":"yu","说":"shuo","讲":"jiang","谈":"tan","论":"lun","议":"yi","评":"ping","判":"pan",
"明":"ming","白":"bai","清":"qing","楚":"chu","细":"xi","粗":"cu","准":"zhun","确":"que","实":"shi",
# 常见姓氏/称谓补充
"王":"wang","李":"li","张":"zhang","刘":"liu","陈":"chen","杨":"yang","赵":"zhao","黄":"huang","周":"zhou",
"吴":"wu","徐":"xu","孙":"sun","胡":"hu","朱":"zhu","高":"gao","林":"lin","何":"he","郭":"guo",
"马":"ma","罗":"luo","梁":"liang","宋":"song","郑":"zheng","谢":"xie","韩":"han","唐":"tang","冯":"feng",
"于":"yu","董":"dong","萧":"xiao","程":"cheng","曹":"cao","袁":"yuan","邓":"deng","许":"xu","傅":"fu",
"沈":"shen","曾":"zeng","彭":"peng","吕":"lv","苏":"su","卢":"lu","蒋":"jiang","蔡":"cai","贾":"jia",
# 爱托皮利卡业务相关高频字
"爱":"ai","托":"tuo","皮":"pi","利":"li","卡":"ka","教":"jiao","育":"yu","儿":"er","童":"tong",
"成":"cheng","长":"zhang","护":"hu","花":"hua","使":"shi","者":"zhe","路":"lu","径":"jing","引":"yin",
"擎":"qing","四":"si","会":"hui","习":"xi","思":"si","考":"kao","活":"huo","用":"yong","方":"fang",
"向":"xiang","平":"ping","台":"tai","美":"mei","术":"shu","音":"yin","乐":"yue","编":"bian","程":"cheng",
"餐":"can","厅":"ting","研":"yan","学":"xue","资":"zi","源":"yuan","能":"neng","力":"li","模":"mo",
"型":"xing","产":"chan","品":"pin","公":"gong","司":"si","品":"pin","牌":"pai","标":"biao","知":"zhi",
"识":"shi","智":"zhi","慧":"hui","未":"wei","来":"lai","未":"wei","定":"ding","义":"yi","生":"sheng",
"命":"ming","运":"yun","营":"ying","销":"xiao","客":"ke","户":"hu","价":"jia","值":"zhi","服":"fu",
"务":"wu","管":"guan","理":"li","创":"chuang","新":"xin",    "团":"tuan","队":"dui","伙":"huo","伴":"ban",
}

# 第二批：THUOCL 高频缺失字补充（无声调；ü 在 l/n 后记作 v，其余记作 u）
CHAR_PINYIN_EXTRA = {
"权":"quan","版":"ban","券":"quan","度":"du","证":"zheng","院":"yuan","制":"zhi","部":"bu","式":"shi","规":"gui","经":"jing","数":"shu","革":"ge","监":"jian","范":"fan","督":"du","场":"chang","执":"zhi","委":"wei","保":"bao","债":"zhai","守":"shou","豆":"dou","违":"wei","商":"shang","犯":"fan","购":"gou","化":"hua","济":"ji","省":"sheng","动":"dong","统":"tong","府":"fu","员":"yuan","承":"cheng","包":"bao","约":"yue","任":"ren","交":"jiao","据":"ju","专":"zhuan","系":"xi","责":"ze","报":"bao","露":"lu","设":"she","构":"gou","局":"ju","协":"xie","京":"jing","注":"zhu","期":"qi","披":"pi","区":"qu","控":"kong","面":"mian","性":"xing","易":"yi","接":"jie","通":"tong","签":"qian","轿":"jiao","量":"liang","支":"zhi","股":"gu","案":"an","限":"xian","序":"xu","效":"xiao","疗":"liao","态":"tai","决":"jue","财":"cai","处":"chu","所":"suo","告":"gao","招":"zhao","表":"biao","牛":"niu","本":"ben","检":"jian","主":"zhu","费":"fei","苹":"ping","器":"qi","加":"jia","达":"da","级":"ji","符":"fu","配":"pei","息":"xi","集":"ji","席":"xi","持":"chi","络":"luo","税":"shui","码":"ma","入":"ru","环":"huan","华":"hua","体":"ti","复":"fu","解":"jie","诈":"zha","率":"lv","置":"zhi","企":"qi","测":"ce","糕":"gao","算":"suan","指":"zhi","欺":"qi","组":"zu","库":"ku","汽":"qi","求":"qiu","汇":"hui","函":"han","图":"tu","章":"zhang","园":"yuan","物":"wu","神":"shen","缺":"que","享":"xiang","精":"jing","单":"dan","预":"yu","基":"ji","结":"jie","迁":"qian","册":"ce","益":"yi","具":"ju","拆":"chai","核":"he","社":"she","元":"yuan","摩":"mo","款":"kuan","越":"yue","特":"te","广":"guang","操":"cao","优":"you","遗":"yi","额":"e","载":"zai","职":"zhi","腐":"fu","消":"xiao","损":"sun","农":"nong","州":"zhou","串":"chuan","试":"shi","流":"liu","默":"mo","融":"rong","象":"xiang","例":"li","猫":"mao","维":"wei","克":"ke","增":"zeng","认":"ren","担":"dan","审":"shen","亚":"ya","迪":"di","录":"lu","始":"shi","宏":"hong","需":"xu","参":"can","端":"duan","球":"qiu","陷":"xian","裁":"cai","萝":"luo","传":"chuan","断":"duan","跨":"kua","号":"hao","卜":"bu","登":"deng","熊":"xiong","防":"fang","破":"po","馆":"guan","装":"zhuang","诺":"nuo","势":"shi","厂":"chang","视":"shi","备":"bei","急":"ji","博":"bo","投":"tou","阴":"yin","印":"yin","奸":"jian","科":"ke","贸":"mao","奥":"ao","仪":"yi","待":"dai","乙":"yi","访":"fang","避":"bi","卫":"wei","归":"gui","糖":"tang","连":"lian","斯":"si","当":"dang","亡":"wang","付":"fu","惠":"hui","粉":"fen","洋":"yang","比":"bi","贿":"hui","割":"ge","战":"zhan","普":"pu","批":"pi","争":"zheng","办":"ban","游":"you","排":"pai","龙":"long","换":"huan","锅":"guo","楼":"lou","输":"shu","储":"chu","佣":"yong","羊":"yang","葡":"pu","尔":"er","萄":"tao","遥":"yao","盘":"pan","巧":"qiao","照":"zhao","占":"zhan","诉":"su","补":"bu","址":"zhi","川":"chuan","盈":"ying","列":"lie","项":"xiang","板":"ban","启":"qi","技":"ji","突":"tu","询":"xun","译":"yi","素":"su","层":"ceng","店":"dian","野":"ye","段":"duan","虚":"xu","起":"qi","恢":"hui","沙":"sha","赂":"lu","贷":"dai","共":"gong","境":"jing","格":"ge","阳":"yang","陆":"lu","福":"fu","偿":"chang","迟":"chi","除":"chu","布":"bu","辩":"bian","移":"yi","缓":"huan","杀":"sha","疾":"ji","桃":"tao","原":"yuan","驾":"jia","罪":"zui","速":"su","伪":"wei","题":"ti","按":"an","援":"yuan","抵":"di","扭":"niu","密":"mi","辖":"xia","联":"lian","令":"ling","矩":"ju","步":"bu","兴":"xing","虐":"nue","垄":"long","兼":"jian","片":"pian","键":"jian","首":"shou","荐":"jian","武":"wu","派":"pai","涨":"zhang","港":"gang","状":"zhuang","毒":"du","欧":"ou","毛":"mao","古":"gu","压":"ya","份":"fen","央":"yang","示":"shi","先":"xian","际":"ji","柿":"shi","牵":"qian","递":"di","柠":"ning","狗":"gou","檬":"meng","超":"chao","析":"xi","围":"wei","节":"jie","封":"feng","渠":"qu","霸":"ba","麻":"ma","竞":"jing","居":"ju","健":"jian","相":"xiang","景":"jing","冒":"mao","酱":"jiang","伤":"shang","挪":"nuo","趋":"qu","扶":"fu","梅":"mei","框":"kuang","边":"bian","哈":"ha","馒":"man","蕉":"jiao","块":"kuai","贴":"tie","洲":"zhou","剂":"ji",
}
CHAR_PINYIN.update(CHAR_PINYIN_EXTRA)
