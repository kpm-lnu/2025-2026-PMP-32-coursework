-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: omeka_museum
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `omeka_collections`
--

DROP TABLE IF EXISTS `omeka_collections`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_collections` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `public` tinyint(4) NOT NULL,
  `featured` tinyint(4) NOT NULL,
  `added` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  `modified` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  `owner_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `public` (`public`),
  KEY `featured` (`featured`),
  KEY `owner_id` (`owner_id`),
  KEY `added` (`added`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_collections`
--

LOCK TABLES `omeka_collections` WRITE;
/*!40000 ALTER TABLE `omeka_collections` DISABLE KEYS */;
INSERT INTO `omeka_collections` VALUES (1,1,0,'2026-05-17 19:19:41','2026-05-17 19:19:41',1),(5,1,0,'2026-05-09 11:49:12','2026-05-09 11:49:12',1),(6,1,0,'2026-05-09 11:49:56','2026-05-09 11:49:56',1),(7,1,0,'2026-05-09 11:50:07','2026-05-09 11:50:14',1),(8,1,0,'2026-05-09 11:50:35','2026-05-09 11:50:35',1);
/*!40000 ALTER TABLE `omeka_collections` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_element_sets`
--

DROP TABLE IF EXISTS `omeka_element_sets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_element_sets` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `record_type` varchar(50) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `record_type` (`record_type`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_element_sets`
--

LOCK TABLES `omeka_element_sets` WRITE;
/*!40000 ALTER TABLE `omeka_element_sets` DISABLE KEYS */;
INSERT INTO `omeka_element_sets` VALUES (1,NULL,'Dublin Core','The Dublin Core metadata element set is common to all Omeka records, including items, files, and collections. For more information see, http://dublincore.org/documents/dces/.'),(3,'Item','Item Type Metadata','The item type metadata element set, consisting of all item type elements bundled with Omeka and all item type elements created by an administrator.');
/*!40000 ALTER TABLE `omeka_element_sets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_element_texts`
--

DROP TABLE IF EXISTS `omeka_element_texts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_element_texts` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `record_id` int(10) unsigned NOT NULL,
  `record_type` varchar(50) NOT NULL,
  `element_id` int(10) unsigned NOT NULL,
  `html` tinyint(4) NOT NULL,
  `text` mediumtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `record_type_record_id` (`record_type`,`record_id`),
  KEY `element_id` (`element_id`),
  KEY `text` (`text`(20)),
  KEY `record_element_text` (`record_type`,`record_id`,`element_id`,`text`(20))
) ENGINE=InnoDB AUTO_INCREMENT=112 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_element_texts`
--

LOCK TABLES `omeka_element_texts` WRITE;
/*!40000 ALTER TABLE `omeka_element_texts` DISABLE KEYS */;
INSERT INTO `omeka_element_texts` VALUES (1,1,'Collection',50,0,'Археологія'),(2,1,'Collection',41,0,'Археологічні знахідки з розкопок на території України'),(5,1,'Item',50,0,' Скляні браслети '),(6,1,'Item',41,0,'Під час розкопок віднайдено фрагменти амфор, які виготовлялися у Візантії, уламки скляних браслетів немісцевого походження'),(7,1,'Item',40,0,'ХІІ–ХІІІ ст.'),(8,1,'Item',38,0,'місто Белз (Сокальський район Львівщини) '),(13,5,'Collection',50,0,'Документи та карти\r\n'),(14,5,'Collection',41,0,'Історичні документи, грамоти, картографічні матеріали та рукописи, що відображають адміністративну та культурну історію Львова і Львівського регіону XVII–XX століть'),(15,6,'Collection',50,0,'Зброя'),(16,6,'Collection',41,0,'Предмети озброєння та військового спорядження різних епох: холодна та вогнепальна зброя, захисне спорядження козацького та середньовічного періодів'),(17,7,'Collection',50,0,'Побут та ремесла'),(18,7,'Collection',41,0,'Предмети повсякденного побуту та народного мистецтва Львівщини XIX–XX століть: вишивка, кераміка, дерев\'яні вироби, металеві предмети домашнього вжитку'),(19,8,'Collection',50,0,'Фотографії'),(20,8,'Collection',41,0,'Фотографічні матеріали кінця XIX – першої половини XX століття, що документують вигляд міста Львова, його вулиць, площ та архітектурних пам\'яток'),(21,2,'Item',50,0,'Старовинний український керамічний глечик, виріб Опішнянської кераміки'),(22,2,'Item',41,0,'Старовинний український керамічний глечик, який є виробом Опішнянської кераміки. Виготовлений вручну, характерний для традиційного гончарства Полтавщини. Прикрашений поливою та мальованим рослинним орнаментом. Глечик використовують для зберігання рідин, головним чином, молочних продуктів (молока, сметани тощо). Незамінний атрибут українського сільського побуту.'),(23,2,'Item',40,0,' XIX ст.'),(24,2,'Item',51,0,'Фізичний об\'єкт'),(25,2,'Item',38,0,'Полтавщина'),(26,3,'Item',50,0,'Кам\'яний наконечник стріли'),(27,3,'Item',41,0,'Крем\'яна стріла. Наконечник до стріли - крем\'яний, червонуватого кольору, трикутноподібної форми, при основі вигнутий до середини. По обох боках лезо ретушоване. Кремнієві та кам\'яні наконечники - інструменти періоду неоліту. Використовувалися людиною у повсякденному житт'),(28,3,'Item',40,0,'Період неоліту'),(29,3,'Item',51,0,'Фізичний об\'єкт'),(30,3,'Item',38,0,'Кременець'),(31,4,'Item',50,0,'Козацькі шаблі. XVII – XVIII ст.'),(32,4,'Item',41,0,'Шабля є різновидом холодної зброї з довгим викривленим клинком, призначена для нанесення рубаючо-ріжучих та колючих ударів. Козаки здебільшого використовували трофейну і покупну зброю, яка походила із різних кутків світу. На території України масово шаблі не виготовлялися, за винятком Львова, який мав розвинені ковальські цехи, але на той момент був під владою Польщі. Серед шабель, які експонуються в Історичному музеї, є шаблі польського, італійського, турецького та козацького виробництва. Вони відрізняються формою та оздобленістю клинка та рукояті. Наприклад, на козацькій шаблі зображено перехрещені булава та пірнач і напис: «За верность земле и преданиям». Шабля один із головних козачих атрибутів, це не просто кривий меч – це символ лицаря і вільної людини. Крім того козаки мали по декілька шабель – «чорну» і «білу», одна була бойовою, а інша парадна, яка носилась на свята.'),(33,4,'Item',40,0,'XVII – XVIII ст.'),(34,4,'Item',51,0,'Фізичний об\'єкт'),(35,4,'Item',38,0,'Дніпропетровська область'),(36,5,'Item',50,0,'Мушкет'),(37,5,'Item',41,0,'Кремінний мушкет виробництва Османської імперії XVIII століття. Зброя потрапила на територію Галичини під час військових конфліктів між Річчю Посполитою та Османською імперією. Відзначається характерним декором ложа з перламутровими інкрустаціями, типовими для османського зброярського мистецтва.'),(38,5,'Item',40,0,'XVIII ст.'),(39,5,'Item',38,0,'Османська імперія,'),(40,6,'Item',50,0,'Мушкет'),(41,6,'Item',41,0,'Кремінний мушкет виробництва Османської імперії XVIII століття. Зброя потрапила на територію Галичини під час військових конфліктів між Річчю Посполитою та Османською імперією. Відзначається характерним декором ложа з перламутровими інкрустаціями, типовими для османського зброярського мистецтва.'),(42,6,'Item',40,0,'XVIII ст.'),(43,6,'Item',38,0,'Османська імперія,'),(48,7,'Item',50,0,'Жіноча вишиванка '),(49,7,'Item',41,0,'\r\nСорочка жіноча вишивка,кінець 19 століття,початок 20 століття'),(50,7,'Item',40,0,'ХІХ ст.'),(51,7,'Item',38,0,'Хмельницька область'),(52,8,'Item',50,0,'Скриня різьблена'),(53,8,'Item',41,0,'тип орнаменту:  геометричний\r\nТехніки:  ковальська техніка / столярна техніка / різьблення плоске / тонування / розпис / вирізування'),(54,8,'Item',40,0,'кінець ХІХ ст.'),(55,8,'Item',51,0,'Фізичний об\'єкт'),(56,8,'Item',38,0,'Гуцульщина'),(57,9,'Item',50,0,'Бойова сокира'),(58,9,'Item',41,0,'Форма цього екземпляру, вочевидь, місцева, аналогії їй відомі та датуються доволі широким часовим періодом Х-ХІІІ століть. Проте мотив орнаменту рідкісний, якщо не сказати – унікальний. За окремими елементами, з яких складається орнамент, його можна датувати в межах вужчого часу, від кінця Х до початку ХІ століть. Цьому відповідає й інкрустація тризубом, іконографія якого датується періодом княжіння Володимира Святославича'),(59,9,'Item',40,0,'Х-ХІІІ ст.'),(60,9,'Item',51,0,'Фізичний об\'єкт'),(61,9,'Item',38,0,'Львівщина'),(62,10,'Item',50,0,'Свічник-трійця'),(63,10,'Item',41,0,'Трійці – це різьблені, часто пишно декоровані трисвічники, які мають церковно-літургійне та обрядово-побутове застосування. Термін «гуцульські та покутські свічники-трійці» давно увійшов у науковий обіг. Цей вислів акцентує, що названий вид дерев’яної пластики характерний лише для Гуцульщини та Покуття. Утім навіть на такій невеликій території трійці побутують вкрай нерівномірно. Аналіз зібраного матеріалу дає можливість простежити походження трисвічників із 37 гуцульських та 42 покутських сіл. що свідчить про винятково локальний характер цього виду народного мистецтва.'),(64,10,'Item',40,0,'Друга пол. ХІХ ст.'),(65,10,'Item',51,0,'Фізичний об\'єкт'),(66,10,'Item',38,0,'с. Нижній Березів Косівського р-ну Івано-Франківської обл.'),(67,11,'Item',50,0,'Австрійська карта Львова 1844 року'),(68,11,'Item',41,0,'План території Львова є оригіналом фотозйомки виконаної Віденським військово-географічним інститутом. План датований 1844 роком. На аркуші плану розміщено прізвища його авторів: Кратохвіль (Kratochwill), Радайчіч (Radaichich), Кранковіч (Krankowich). \r\nЛегенда:\r\n\r\nУ правому верхньому куті розташовано назву: \"Лемберг з його передмістями у 1844 році\" (Lemberg mit seinen Vorstadten im Jahre 1844).\r\nНижче розміщено мірну лінію із написом: \"1 віденському дюйму відповідає 100 сажнів або 250 кроків на місцевості\" (1 Wiener Zoll = 100 Klafter oder 250 Schritte). Масштаб плану в числовому еквіваленті - 1:7 200 [12], c. 228.\r\nПісля мірної лінії розташовано перелік умовних позначень та інформацію про поділ міста на передмістя:\r\n\"Перша дільниця або Галицьке передмістя\" (1-tes Viertel oder Halitcher Vorstadt).\r\n\"Друга дільниця або Краківське передмістя\" (2-tes Viertel oder Krakauer Vorstadt).\r\n\"Третя дільниця або Жовківське передмістя\" (3-tes Viertel oder Żolkiewer Vorstadt).\r\n\"Четверта дільниця або Бродівське передмістя\" (4-tes Viertel oder Brodyer Vorstadt).\r\n\"Місто\" (Stadt).\r\nУ правому нижньому куті міститься перелік із 26 важливих будівель в Середмісті (Bezeichnung der vorzüglichsten Gebaede in der Stadt).\r\nНижче розміщено напис (auf Stein gest. und [] Kratochwill und Rado[iс]sich geschrieben Krankowich).\r\nУ правому лівому куті розташовано перелік із 91-ї важливої будівлі на територіях чотирьох дільниць міста (Bezeichnung der vorzüglichsten Gebaede in der Stadt).'),(69,11,'Item',40,0,'1844'),(70,11,'Item',51,0,'Картографічний матеріал'),(71,11,'Item',38,0,'Львів'),(72,12,'Item',50,0,'Грамота базельського синоду'),(73,12,'Item',41,0,'Документ оздоблений декоративним заголовком та вислою металевою печаткою, яка підтверджує його автентичність.\r\nрамота написана в період роботи Базельського собору католицької церкви (1431–1449), скликаного папою Мартином V для реформування церкви та врегулювання військового конфлікту з гуситами. Відповідно до неї львівському архієпископу Одровонжу Івану передавалася частина судових і адміністративних повноважень. Ця грамота фактично посилювала автономію Львівської архідієцезії, дозволяючи вирішувати частину таких справ на місці, без апеляції до Риму. Це прискорювало судочинство і зміцнювало роль архієпископа в регіоні.'),(74,12,'Item',40,0,'1431–1449'),(75,12,'Item',51,0,'Текстовий документ'),(76,12,'Item',38,0,'Зберігається у Центральному державному сторичному архіві України, м. Львів, (фонд № 131 «Колекція грамот на пергаменті» , оп. 1, спр. 119).'),(77,13,'Item',50,0,'Вид центру Львова 1924 року'),(78,13,'Item',41,0,'У 1924 році Львів, місто з багатовіковою історією, переживало період значних змін та трансформацій. Після буремних років Першої світової війни та польсько-української війни 1918-1919 років місто опинилося у складі Другої Польської Республіки. Згідно з Ризьким мирним договором 1921 року, Львів став адміністративним центром Львівського воєводства.\r\nНа початку 1924 року посаду воєводи Львівського воєводства обіймав Kazimierz Grabowski (Казімєж Грабовський), який був звільнений з цієї посади 30 червня 1924 року. Після нього короткий період обов’язки виконував Stanisław Zimny (Станіслав Зимний), а потім на цю посаду був призначений Paweł Garapich (Павел Гарапіх), який залишався воєводою до 1927 року​. Міським головою Львова в цей час був Józef Neumann (Йозеф Нойманн) який обіймав цю посаду з 1918 до 1927 року.'),(79,13,'Item',40,0,'1924р'),(80,13,'Item',51,0,'Зображення'),(81,13,'Item',38,0,'Львів'),(82,14,'Item',50,0,'Карта Боплана'),(83,14,'Item',41,0,'Культурно-просвітницький центр Alex Art House – це три галереї приватних колекцій та Музей стародавньої книги. Основу експозиції галерей складають… карти. Зокрема карти французького картографа та інженера Ґійома Левассера де Боплана. Серед раритетів – астрономічні карти німецького астронома і математика 17 століття  Йоганна Доппельмайра. Особливу історичну цінність мають дві карти зображення України 1478 року з Римського видання географічної праці Клавдія Птолемея «Космографія». Ці карти належать до ранніх зразків гравюри на міді і є одними з перших в історії друкованих карт.\r\n\r\n'),(84,14,'Item',40,0,'1478\r\n'),(85,14,'Item',51,0,'Картографічний матеріал'),(86,14,'Item',38,0,'Київщина'),(87,15,'Item',50,0,'Личаківський цвинтар початку XX століття'),(88,15,'Item',41,0,'Історія цвинтаря починається з 1786 року після заборони здійснювати поховання навколо храмів у межах міста. Личаківський цвинтар один з чотирьох, які тоді функціонували у Львові, і єдиний, який зберігся до сьогодні. Але знайти поховання, які з’являлися тут у ті роки, майже неможливо, бо в середині ХІХ ст. почало діяти нововведення магістрату, яке передбачало встановлення каменедробарки на кладовищі. Так, надгробки над могилами, які не доглядали родичі упродовж 25 років, перемелювали на дрібне каміння, яким вистеляли доріжки, а пізніше збудували цвинтарну браму.'),(89,15,'Item',40,0,'1900'),(90,15,'Item',51,0,'Зображення'),(91,15,'Item',38,0,'Львів'),(92,16,'Item',50,0,'Діорама «Поховання знатного скіфа»'),(93,16,'Item',41,0,'Діорама відтворює обряд поховання знатного представника скіфської культури. Скіфи — кочовий іраномовний народ, що населяв територію Північного Причорномор\'я у VII–III століттях до нашої ери. Поховальний обряд знатних скіфів відрізнявся особливою пишністю: разом із небіжчиком у курган клали зброю, коштовності, посуд та жертвували коней. Діорама є реконструкцією на основі археологічних матеріалів скіфських курганів.'),(94,16,'Item',40,0,'VII–III ст. до н.е.'),(95,16,'Item',51,0,'Діорама'),(96,16,'Item',38,0,'Північне Причорномор\'я'),(97,17,'Item',50,0,'Діорама «Київ. Місто Володимира»'),(98,17,'Item',41,0,'Діорама відтворює вигляд давньоруського Києва часів князя Володимира Великого (980–1015 рр.). Місто Володимира — укріплена частина Києва, збудована за часів правління князя Володимира Святославича. Включала Десятинну церкву, князівський палац та систему укріплень. Саме тут у 988 році відбулося хрещення Русі. Діорама створена на основі археологічних досліджень та історичних джерел.'),(99,17,'Item',40,0,'X–XI ст.'),(100,17,'Item',51,0,'Діорама'),(101,17,'Item',38,0,'Київ, Київська Русь'),(102,18,'Item',50,0,'Копія Золотої пекторалі'),(103,18,'Item',41,0,'Копія знаменитої золотої пекторалі — нагрудної прикраси скіфського царя, знайденої у кургані Товста Могила на Дніпропетровщині у 1971 році археологом Борисом Мозолевським. Оригінал датується IV століттям до нашої ери та зберігається у Національному музеї історії України у Києві. Пектораль важить 1148 грамів та має діаметр 30,6 см. Складається з трьох ярусів: нижній зображує сцени боротьби тварин, середній — рослинний орнамент, верхній — сцени мирного скіфського побуту. Вважається шедевром ювелірного мистецтва античного світу.'),(104,18,'Item',40,0,'IV ст. до н.е. (копія — XX ст.)'),(105,18,'Item',51,0,'Ювелірний виріб (копія)'),(106,18,'Item',38,0,'Дніпропетровська область, курган Товста Могила'),(107,19,'Item',50,0,'Фунікулер'),(108,19,'Item',41,0,'Київський фунікулер — канатний підйомник, збудований у 1905 році для зв\'язку Верхнього міста з Подолом. Споруджений на залізобетонній естакаді з прокладеними рейками. Став вирішенням транспортної проблеми крутих схилів між двома частинами міста. Один з найстаріших фунікулерів на території України, що функціонує донині.'),(109,19,'Item',40,0,'1905'),(110,19,'Item',51,0,'Зображення'),(111,19,'Item',38,0,'Київ');
/*!40000 ALTER TABLE `omeka_element_texts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_elements`
--

DROP TABLE IF EXISTS `omeka_elements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_elements` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `element_set_id` int(10) unsigned NOT NULL,
  `order` int(10) unsigned DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `comment` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_element_set_id` (`element_set_id`,`name`),
  UNIQUE KEY `order_element_set_id` (`element_set_id`,`order`),
  KEY `element_set_id` (`element_set_id`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_elements`
--

LOCK TABLES `omeka_elements` WRITE;
/*!40000 ALTER TABLE `omeka_elements` DISABLE KEYS */;
INSERT INTO `omeka_elements` VALUES (1,3,NULL,'Text','Any textual data included in the document',NULL),(2,3,NULL,'Interviewer','The person(s) performing the interview',NULL),(3,3,NULL,'Interviewee','The person(s) being interviewed',NULL),(4,3,NULL,'Location','The location of the interview',NULL),(5,3,NULL,'Transcription','Any written text transcribed from a sound',NULL),(6,3,NULL,'Local URL','The URL of the local directory containing all assets of the website',NULL),(7,3,NULL,'Original Format','The type of object, such as painting, sculpture, paper, photo, and additional data',NULL),(10,3,NULL,'Physical Dimensions','The actual physical size of the original image',NULL),(11,3,NULL,'Duration','Length of time involved (seconds, minutes, hours, days, class periods, etc.)',NULL),(12,3,NULL,'Compression','Type/rate of compression for moving image file (i.e. MPEG-4)',NULL),(13,3,NULL,'Producer','Name (or names) of the person who produced the video',NULL),(14,3,NULL,'Director','Name (or names) of the person who produced the video',NULL),(15,3,NULL,'Bit Rate/Frequency','Rate at which bits are transferred (i.e. 96 kbit/s would be FM quality audio)',NULL),(16,3,NULL,'Time Summary','A summary of an interview given for different time stamps throughout the interview',NULL),(17,3,NULL,'Email Body','The main body of the email, including all replied and forwarded text and headers',NULL),(18,3,NULL,'Subject Line','The content of the subject line of the email',NULL),(19,3,NULL,'From','The name and email address of the person sending the email',NULL),(20,3,NULL,'To','The name(s) and email address(es) of the person to whom the email was sent',NULL),(21,3,NULL,'CC','The name(s) and email address(es) of the person to whom the email was carbon copied',NULL),(22,3,NULL,'BCC','The name(s) and email address(es) of the person to whom the email was blind carbon copied',NULL),(23,3,NULL,'Number of Attachments','The number of attachments to the email',NULL),(24,3,NULL,'Standards','',NULL),(25,3,NULL,'Objectives','',NULL),(26,3,NULL,'Materials','',NULL),(27,3,NULL,'Lesson Plan Text','',NULL),(28,3,NULL,'URL','',NULL),(29,3,NULL,'Event Type','',NULL),(30,3,NULL,'Participants','Names of individuals or groups participating in the event',NULL),(31,3,NULL,'Birth Date','',NULL),(32,3,NULL,'Birthplace','',NULL),(33,3,NULL,'Death Date','',NULL),(34,3,NULL,'Occupation','',NULL),(35,3,NULL,'Biographical Text','',NULL),(36,3,NULL,'Bibliography','',NULL),(37,1,8,'Contributor','An entity responsible for making contributions to the resource',NULL),(38,1,15,'Coverage','The spatial or temporal topic of the resource, the spatial applicability of the resource, or the jurisdiction under which the resource is relevant',NULL),(39,1,4,'Creator','An entity primarily responsible for making the resource',NULL),(40,1,7,'Date','A point or period of time associated with an event in the lifecycle of the resource',NULL),(41,1,3,'Description','An account of the resource',NULL),(42,1,11,'Format','The file format, physical medium, or dimensions of the resource',NULL),(43,1,14,'Identifier','An unambiguous reference to the resource within a given context',NULL),(44,1,12,'Language','A language of the resource',NULL),(45,1,6,'Publisher','An entity responsible for making the resource available',NULL),(46,1,10,'Relation','A related resource',NULL),(47,1,9,'Rights','Information about rights held in and over the resource',NULL),(48,1,5,'Source','A related resource from which the described resource is derived',NULL),(49,1,2,'Subject','The topic of the resource',NULL),(50,1,1,'Title','A name given to the resource',NULL),(51,1,13,'Type','The nature or genre of the resource',NULL);
/*!40000 ALTER TABLE `omeka_elements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_exhibit_block_attachments`
--

DROP TABLE IF EXISTS `omeka_exhibit_block_attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_exhibit_block_attachments` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `block_id` int(10) unsigned NOT NULL,
  `item_id` int(10) unsigned NOT NULL,
  `file_id` int(10) unsigned DEFAULT NULL,
  `caption` text DEFAULT NULL,
  `order` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `block_id_order` (`block_id`,`order`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_exhibit_block_attachments`
--

LOCK TABLES `omeka_exhibit_block_attachments` WRITE;
/*!40000 ALTER TABLE `omeka_exhibit_block_attachments` DISABLE KEYS */;
INSERT INTO `omeka_exhibit_block_attachments` VALUES (1,1,19,19,NULL,1),(2,1,17,17,NULL,2);
/*!40000 ALTER TABLE `omeka_exhibit_block_attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_exhibit_page_blocks`
--

DROP TABLE IF EXISTS `omeka_exhibit_page_blocks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_exhibit_page_blocks` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `page_id` int(10) unsigned NOT NULL,
  `layout` varchar(50) NOT NULL,
  `options` text DEFAULT NULL,
  `text` mediumtext DEFAULT NULL,
  `order` smallint(5) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `page_id_order` (`page_id`,`order`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_exhibit_page_blocks`
--

LOCK TABLES `omeka_exhibit_page_blocks` WRITE;
/*!40000 ALTER TABLE `omeka_exhibit_page_blocks` DISABLE KEYS */;
INSERT INTO `omeka_exhibit_page_blocks` VALUES (1,1,'file-text','{\"file-position\":\"left\",\"file-size\":\"fullsize\",\"captions-position\":\"center\"}',NULL,1);
/*!40000 ALTER TABLE `omeka_exhibit_page_blocks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_exhibit_pages`
--

DROP TABLE IF EXISTS `omeka_exhibit_pages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_exhibit_pages` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `exhibit_id` int(10) unsigned NOT NULL,
  `parent_id` int(10) unsigned DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `short_title` varchar(255) DEFAULT NULL,
  `slug` varchar(30) NOT NULL,
  `order` smallint(5) unsigned DEFAULT NULL,
  `added` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  `modified` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  PRIMARY KEY (`id`),
  UNIQUE KEY `exhibit_id_parent_id_slug` (`exhibit_id`,`parent_id`,`slug`),
  KEY `exhibit_id_order` (`exhibit_id`,`order`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_exhibit_pages`
--

LOCK TABLES `omeka_exhibit_pages` WRITE;
/*!40000 ALTER TABLE `omeka_exhibit_pages` DISABLE KEYS */;
INSERT INTO `omeka_exhibit_pages` VALUES (1,1,NULL,'Київ','','--------',0,'2026-05-09 22:11:18','2026-05-09 22:12:33');
/*!40000 ALTER TABLE `omeka_exhibit_pages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_exhibits`
--

DROP TABLE IF EXISTS `omeka_exhibits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_exhibits` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `credits` text DEFAULT NULL,
  `featured` tinyint(1) DEFAULT 0,
  `public` tinyint(1) DEFAULT 0,
  `theme` varchar(30) DEFAULT NULL,
  `theme_options` text DEFAULT NULL,
  `slug` varchar(30) NOT NULL,
  `added` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  `modified` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  `owner_id` int(10) unsigned DEFAULT NULL,
  `use_summary_page` tinyint(1) DEFAULT 1,
  `cover_image_file_id` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`),
  KEY `public` (`public`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_exhibits`
--

LOCK TABLES `omeka_exhibits` WRITE;
/*!40000 ALTER TABLE `omeka_exhibits` DISABLE KEYS */;
INSERT INTO `omeka_exhibits` VALUES (1,'Київ у минулому столітті','','',0,1,'berlin',NULL,'------------------------------','2026-05-09 22:10:07','2026-05-09 22:12:33',1,1,NULL);
/*!40000 ALTER TABLE `omeka_exhibits` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_feedbacks`
--

DROP TABLE IF EXISTS `omeka_feedbacks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_feedbacks` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `inserted` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_feedbacks`
--

LOCK TABLES `omeka_feedbacks` WRITE;
/*!40000 ALTER TABLE `omeka_feedbacks` DISABLE KEYS */;
INSERT INTO `omeka_feedbacks` VALUES (1,'Іван','admin@museum.ua','Дуже сподобався музей','2026-05-09 19:04:13'),(2,'Ірина','museum@museum.ua','Супер','2026-05-09 19:07:44');
/*!40000 ALTER TABLE `omeka_feedbacks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_files`
--

DROP TABLE IF EXISTS `omeka_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_files` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `item_id` int(10) unsigned NOT NULL,
  `order` int(10) unsigned DEFAULT NULL,
  `size` bigint(20) unsigned NOT NULL,
  `has_derivative_image` tinyint(1) NOT NULL,
  `authentication` char(32) DEFAULT NULL,
  `mime_type` varchar(255) DEFAULT NULL,
  `type_os` varchar(255) DEFAULT NULL,
  `filename` text NOT NULL,
  `original_filename` text NOT NULL,
  `modified` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `added` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  `stored` tinyint(1) NOT NULL DEFAULT 0,
  `metadata` mediumtext NOT NULL,
  `alt_text` mediumtext DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_files`
--

LOCK TABLES `omeka_files` WRITE;
/*!40000 ALTER TABLE `omeka_files` DISABLE KEYS */;
INSERT INTO `omeka_files` VALUES (1,1,NULL,42765,0,'417889b6f4f712a6f5c40aca37fcc6f9','image/jpeg','','4aab3b90ed12be13b01ffae597031767.jpg','4381439-4.jpg','2026-05-09 17:04:10','2026-05-17 19:37:03',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":600,\"resolution_y\":388,\"compression_ratio\":0.061232817869415805}}',NULL),(2,2,NULL,453775,0,'bc294e235b8e4603538b81c743337b04','image/jpeg','','dbe8da2cf292882ac65dc376eddafc3f.jpg','Старовинний_український_керамічний_глечик,_виріб_Опішнянської_кераміки._03.jpg','2026-05-09 12:44:27','2026-05-09 12:44:27',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":960,\"resolution_y\":1707,\"compression_ratio\":0.09230273221376033}}',NULL),(3,3,NULL,89749,0,'13b6c677757e099956f895549bece561','image/jpeg','','285a2bf27109a52119b8a0373c5229f3.jpg','7-855-277259.jpg','2026-05-09 14:57:14','2026-05-09 14:57:05',1,'0',NULL),(4,4,NULL,198564,0,'0b02f5b7bc473ba09ed01eb4d92c1de9','image/png','','2df91e8a75243a9d9468d13204e3e38a.png','2022-02-16_181543-e1645028257357.png','2026-05-09 15:04:34','2026-05-09 15:04:34',1,'{\"mime_type\":\"image\\/png\",\"video\":{\"dataformat\":\"png\",\"lossless\":false,\"resolution_x\":528,\"resolution_y\":352,\"bits_per_sample\":24,\"compression_ratio\":0.3561251721763085},\"comments\":{\"date:create\":[\"2022-02-16T16:17:26+00:00\"],\"date:modify\":[\"2022-02-16T16:17:25+00:00\"]},\"comments_html\":{\"date:create\":[\"2022-02-16T16:17:26+00:00\"],\"date:modify\":[\"2022-02-16T16:17:25+00:00\"]}}',NULL),(5,5,NULL,61502,0,'9b415177bf1170b9b9f986e2bdd13d3b','image/jpeg','','c59614b286de3600bca21d4025cf4d3c.jpg','030e4eb7638e412f94f58c56b65b5736.jpg','2026-05-09 15:27:39','2026-05-09 15:27:23',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":535,\"resolution_y\":600,\"compression_ratio\":0.063865005192108}}',NULL),(6,6,NULL,61502,0,'9b415177bf1170b9b9f986e2bdd13d3b','image/jpeg','','70a17da3ce327d30629ce70edff204a7.jpg','030e4eb7638e412f94f58c56b65b5736.jpg','2026-05-09 16:21:22','2026-05-09 15:27:24',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":535,\"resolution_y\":600,\"compression_ratio\":0.063865005192108}}',NULL),(7,7,NULL,248977,0,'cdbe22f3b7c05ee3f02401351d82ebc1','image/jpeg','','1c8053aecd41a05f0ef5c73ca24f58c6.jpg','111818138.jpg','2026-05-09 15:51:11','2026-05-09 15:51:11',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":554,\"resolution_y\":738,\"compression_ratio\":0.20298869354517854}}',NULL),(8,8,NULL,116135,0,'adc40665ca2a1f8ea5bf798866fb4f78','image/jpeg','','57e4d38eaf7d27e176df06d5e9c47481.jpg','a4a1f35ec62badf1a25228a7201ed2a0.jpg','2026-05-09 15:57:34','2026-05-09 15:57:06',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":1198,\"resolution_y\":1080,\"compression_ratio\":0.02991997980172716}}',NULL),(9,9,NULL,76627,0,'3487217c995a4c2338fe5554bb745773','image/jpeg','','e3a4b456a33e53a70b36c0987e1d223e.jpg','FB_IMG_1629323766361.max-1920x1080.jpg','2026-05-09 16:01:52','2026-05-09 16:01:52',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":1080,\"resolution_y\":894,\"compression_ratio\":0.026454483939569697}}',NULL),(10,10,NULL,98778,0,'4edf89c9e6c9a2d8b10426d586ea3eb9','image/jpeg','','26afb13676232c565b240d564dfdbd2a.jpg','image31.jpg','2026-05-09 16:05:31','2026-05-09 16:05:31',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":585,\"resolution_y\":800,\"compression_ratio\":0.07035470085470086},\"comments\":{\"IPTCEnvelope\":{\"EnvelopeRecordVersion\":[\"\\u0004\"],\"CodedCharacterSet\":[\"\\u001b%G\"]},\"IPTCApplication\":{\"ApplicationRecordVersion\":[\"\\u0004\"],\"DateCreated\":[\"20120829\"],\"TimeCreated\":[\"172503+0300\"],\"By-line\":[\"Picasa\"]}},\"comments_html\":{\"IPTCEnvelope\":{\"EnvelopeRecordVersion\":[\"\\u0004\"],\"CodedCharacterSet\":[\"\\u001b%G\"]},\"IPTCApplication\":{\"ApplicationRecordVersion\":[\"\\u0004\"],\"DateCreated\":[\"20120829\"],\"TimeCreated\":[\"172503+0300\"],\"By-line\":[\"Picasa\"]}},\"iptc\":{\"comments\":{\"IPTCEnvelope\":{\"EnvelopeRecordVersion\":[\"\\u0000\\u0004\"],\"CodedCharacterSet\":[\"\\u001b%G\"]},\"IPTCApplication\":{\"ApplicationRecordVersion\":[\"\\u0000\\u0004\"],\"DateCreated\":[\"20120829\"],\"TimeCreated\":[\"172503+0300\"],\"By-line\":[\"Picasa\"]}},\"encoding\":\"ISO-8859-1\"},\"jpg\":{\"exif\":{\"FILE\":{\"FileName\":\"26afb13676232c565b240d564dfdbd2a.jpg\",\"FileDateTime\":1778346330,\"FileSize\":98778,\"FileType\":2,\"MimeType\":\"image\\/jpeg\",\"SectionsFound\":\"ANY_TAG, IFD0, THUMBNAIL, EXIF, INTEROP\"},\"COMPUTED\":{\"html\":\"width=\\\"585\\\" height=\\\"800\\\"\",\"Height\":800,\"Width\":585,\"IsColor\":1,\"ByteOrderMotorola\":0,\"Thumbnail.FileType\":2,\"Thumbnail.MimeType\":\"image\\/jpeg\"},\"IFD0\":{\"Software\":\"Picasa\",\"DateTime\":\"2012:08:29 19:29:56\",\"Artist\":\"Picasa\",\"Exif_IFD_Pointer\":96},\"THUMBNAIL\":{\"Compression\":6,\"XResolution\":72,\"YResolution\":72,\"ResolutionUnit\":2,\"JPEGInterchangeFormat\":364,\"JPEGInterchangeFormatLength\":6311},\"EXIF\":{\"ExifVersion\":220,\"DateTimeOriginal\":\"2012:08:29 17:25:03\",\"ExifImageWidth\":585,\"ExifImageLength\":800,\"InteroperabilityOffset\":228,\"ImageUniqueID\":\"999ffccb5f7c17077686b2d61bb522e6\"},\"INTEROP\":{\"InterOperabilityVersion\":\"0100\",\"RelatedImageWidth\":2406,\"RelatedImageHeight\":3293}}}}',NULL),(11,11,NULL,319869,0,'5551cb38742a4c57b5da78c3b7a28376','image/jpeg','','a2997bef6049af51b1c2601cad8d9d0c.jpg','81797_ca_object_representations_media_53800_large.jpg','2026-05-09 16:16:18','2026-05-09 16:10:23',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":700,\"resolution_y\":618,\"compression_ratio\":0.24647018030513176}}',NULL),(12,12,NULL,139866,0,'05b50f9b2952b50e58e0bdcf28bc317b','image/jpeg','','ffb85835adbb20df36cf80be0f85e451.jpg','53e329113067a07672bb21cd9cd4f097c3d41399-jpg_1200.jpg','2026-05-09 16:16:04','2026-05-09 16:13:36',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":1200,\"resolution_y\":824,\"compression_ratio\":0.04715008090614887}}',NULL),(13,13,NULL,703688,0,'32677b0c8de501ec99e49de1a5993936','image/png','','fd74916a5120549daa1db32af273b20b.png','32677b0c8de501ec99e49de1a5993936.png','2026-05-09 16:15:37','2026-05-09 16:15:37',1,'{\"mime_type\":\"image\\/png\",\"video\":{\"dataformat\":\"png\",\"lossless\":false,\"resolution_x\":693,\"resolution_y\":491,\"bits_per_sample\":24,\"compression_ratio\":0.689356958196062}}',NULL),(14,14,NULL,197146,0,'39cd868ad317bdce892114df07ccb8a8','image/jpeg','','78cd72a9cf41847f3038473ae40ff156.jpg','2685769_800x600_KartaBoplanaviki.jpg','2026-05-09 16:19:24','2026-05-09 16:19:24',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":764,\"resolution_y\":600,\"compression_ratio\":0.14335805700988946}}',NULL),(15,15,NULL,472967,0,'6e6d8c284e8e8c7bd1bad911cae25d6d','image/jpeg','','2708f35282c9bc23f10b2c53e46bbf07.jpg','luch1.jpg','2026-05-09 16:21:02','2026-05-09 16:21:02',1,'0',NULL),(16,16,NULL,399425,0,'919df239dc973b1f2970c9e06c29cd4a','image/jpeg','','d698b477dcf4eb79ae8c3102c7a1725e.jpg','Киевский_археологический_музей,_диорама_1.jpg','2026-05-09 16:24:18','2026-05-09 16:24:18',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":1280,\"resolution_y\":853,\"compression_ratio\":0.12194247020320438}}',NULL),(17,17,NULL,332105,0,'c42e019d46d3e7ec5e318cfa18c24e06','image/jpeg','','bbc1092a8abe812710103bb5d89cfb11.jpg','1280px-Киевский_археологический_музей,_диорама_3.jpg','2026-05-09 16:25:39','2026-05-09 16:25:39',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":1280,\"resolution_y\":853,\"compression_ratio\":0.101390008304025}}',NULL),(18,18,NULL,596956,0,'f6fc69713e6919d618c85fb705d78240','image/jpeg','','23f2377a6f4cfe20176b586a953a3aec.jpg','1280px-Киевский_археологический_музей,_пектораль.jpg','2026-05-09 16:27:10','2026-05-09 16:27:10',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":1280,\"resolution_y\":1035,\"compression_ratio\":0.15020028180354267}}',NULL),(19,19,NULL,207994,0,'af2230e640d14f9bc8e82b1c3cc79fa0','image/jpeg','','fbdf2a9b6540b44947259b7052bf51fd.jpg','f1a.jpg','2026-05-09 16:50:06','2026-05-09 16:50:06',1,'{\"mime_type\":\"image\\/jpeg\",\"video\":{\"dataformat\":\"jpg\",\"lossless\":false,\"bits_per_sample\":24,\"pixel_aspect_ratio\":1,\"resolution_x\":960,\"resolution_y\":720,\"compression_ratio\":0.10030574845679012}}',NULL);
/*!40000 ALTER TABLE `omeka_files` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_item_types`
--

DROP TABLE IF EXISTS `omeka_item_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_item_types` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_item_types`
--

LOCK TABLES `omeka_item_types` WRITE;
/*!40000 ALTER TABLE `omeka_item_types` DISABLE KEYS */;
INSERT INTO `omeka_item_types` VALUES (1,'Text','A resource consisting primarily of words for reading. Examples include books, letters, dissertations, poems, newspapers, articles, archives of mailing lists. Note that facsimiles or images of texts are still of the genre Text.'),(3,'Moving Image','A series of visual representations imparting an impression of motion when shown in succession. Examples include animations, movies, television programs, videos, zoetropes, or visual output from a simulation.'),(4,'Oral History','A resource containing historical information obtained in interviews with persons having firsthand knowledge.'),(5,'Sound','A resource primarily intended to be heard. Examples include a music playback file format, an audio compact disc, and recorded speech or sounds.'),(6,'Still Image','A static visual representation. Examples include paintings, drawings, graphic designs, plans and maps. Recommended best practice is to assign the type Text to images of textual materials.'),(7,'Website','A resource comprising of a web page or web pages and all related assets ( such as images, sound and video files, etc. ).'),(8,'Event','A non-persistent, time-based occurrence. Metadata for an event provides descriptive information that is the basis for discovery of the purpose, location, duration, and responsible agents associated with an event. Examples include an exhibition, webcast, conference, workshop, open day, performance, battle, trial, wedding, tea party, conflagration.'),(9,'Email','A resource containing textual messages and binary attachments sent electronically from one person to another or one person to many people.'),(10,'Lesson Plan','A resource that gives a detailed description of a course of instruction.'),(11,'Hyperlink','A link, or reference, to another resource on the Internet.'),(12,'Person','An individual.'),(13,'Interactive Resource','A resource requiring interaction from the user to be understood, executed, or experienced. Examples include forms on Web pages, applets, multimedia learning objects, chat services, or virtual reality environments.'),(14,'Dataset','Data encoded in a defined structure. Examples include lists, tables, and databases. A dataset may be useful for direct machine processing.'),(15,'Physical Object','An inanimate, three-dimensional object or substance. Note that digital representations of, or surrogates for, these objects should use Moving Image, Still Image, Text or one of the other types.'),(16,'Service','A system that provides one or more functions. Examples include a photocopying service, a banking service, an authentication service, interlibrary loans, a Z39.50 or Web server.'),(17,'Software','A computer program in source or compiled form. Examples include a C source file, MS-Windows .exe executable, or Perl script.');
/*!40000 ALTER TABLE `omeka_item_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_item_types_elements`
--

DROP TABLE IF EXISTS `omeka_item_types_elements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_item_types_elements` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `item_type_id` int(10) unsigned NOT NULL,
  `element_id` int(10) unsigned NOT NULL,
  `order` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_type_id_element_id` (`item_type_id`,`element_id`),
  KEY `item_type_id` (`item_type_id`),
  KEY `element_id` (`element_id`)
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_item_types_elements`
--

LOCK TABLES `omeka_item_types_elements` WRITE;
/*!40000 ALTER TABLE `omeka_item_types_elements` DISABLE KEYS */;
INSERT INTO `omeka_item_types_elements` VALUES (1,1,7,NULL),(2,1,1,NULL),(3,6,7,NULL),(6,6,10,NULL),(7,3,7,NULL),(8,3,11,NULL),(9,3,12,NULL),(10,3,13,NULL),(11,3,14,NULL),(12,3,5,NULL),(13,5,7,NULL),(14,5,11,NULL),(15,5,15,NULL),(16,5,5,NULL),(17,4,7,NULL),(18,4,11,NULL),(19,4,15,NULL),(20,4,5,NULL),(21,4,2,NULL),(22,4,3,NULL),(23,4,4,NULL),(24,4,16,NULL),(25,9,17,NULL),(26,9,18,NULL),(27,9,20,NULL),(28,9,19,NULL),(29,9,21,NULL),(30,9,22,NULL),(31,9,23,NULL),(32,10,24,NULL),(33,10,25,NULL),(34,10,26,NULL),(35,10,11,NULL),(36,10,27,NULL),(37,7,6,NULL),(38,11,28,NULL),(39,8,29,NULL),(40,8,30,NULL),(41,8,11,NULL),(42,12,31,NULL),(43,12,32,NULL),(44,12,33,NULL),(45,12,34,NULL),(46,12,35,NULL),(47,12,36,NULL);
/*!40000 ALTER TABLE `omeka_item_types_elements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_item_views`
--

DROP TABLE IF EXISTS `omeka_item_views`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_item_views` (
  `item_id` int(10) unsigned NOT NULL,
  `views` int(10) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_item_views`
--

LOCK TABLES `omeka_item_views` WRITE;
/*!40000 ALTER TABLE `omeka_item_views` DISABLE KEYS */;
INSERT INTO `omeka_item_views` VALUES (1,35),(15,1),(17,16),(18,47),(19,2);
/*!40000 ALTER TABLE `omeka_item_views` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_items`
--

DROP TABLE IF EXISTS `omeka_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_items` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `item_type_id` int(10) unsigned DEFAULT NULL,
  `collection_id` int(10) unsigned DEFAULT NULL,
  `featured` tinyint(4) NOT NULL,
  `public` tinyint(4) NOT NULL,
  `modified` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `added` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  `owner_id` int(10) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `item_type_id` (`item_type_id`),
  KEY `collection_id` (`collection_id`),
  KEY `public` (`public`),
  KEY `featured` (`featured`),
  KEY `owner_id` (`owner_id`),
  KEY `added` (`added`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_items`
--

LOCK TABLES `omeka_items` WRITE;
/*!40000 ALTER TABLE `omeka_items` DISABLE KEYS */;
INSERT INTO `omeka_items` VALUES (1,NULL,1,0,1,'2026-05-09 17:04:10','2026-05-17 19:37:03',1),(2,NULL,7,0,1,'2026-05-09 12:44:27','2026-05-09 11:58:22',1),(3,NULL,1,0,1,'2026-05-09 14:57:14','2026-05-09 14:57:05',1),(4,NULL,6,0,1,'2026-05-09 15:04:34','2026-05-09 15:04:34',1),(5,NULL,6,0,1,'2026-05-09 15:27:39','2026-05-09 15:27:23',1),(6,NULL,6,0,1,'2026-05-09 16:21:22','2026-05-09 15:27:24',1),(7,NULL,7,0,1,'2026-05-09 15:51:11','2026-05-09 15:51:11',1),(8,NULL,7,0,1,'2026-05-09 15:57:34','2026-05-09 15:57:06',1),(9,NULL,6,0,1,'2026-05-09 16:01:52','2026-05-09 16:01:52',1),(10,NULL,7,0,1,'2026-05-09 16:05:31','2026-05-09 16:05:31',1),(11,NULL,5,0,1,'2026-05-09 16:16:18','2026-05-09 16:10:23',1),(12,NULL,5,0,1,'2026-05-09 16:16:04','2026-05-09 16:13:36',1),(13,NULL,8,0,1,'2026-05-09 16:15:37','2026-05-09 16:15:37',1),(14,NULL,5,0,1,'2026-05-09 16:19:24','2026-05-09 16:19:24',1),(15,NULL,8,0,1,'2026-05-09 16:21:02','2026-05-09 16:21:02',1),(16,NULL,1,0,1,'2026-05-09 16:24:18','2026-05-09 16:24:18',1),(17,NULL,1,0,1,'2026-05-09 16:25:39','2026-05-09 16:25:39',1),(18,NULL,1,0,1,'2026-05-09 16:27:10','2026-05-09 16:27:10',1),(19,NULL,8,0,1,'2026-05-09 16:50:06','2026-05-09 16:36:45',1);
/*!40000 ALTER TABLE `omeka_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_keys`
--

DROP TABLE IF EXISTS `omeka_keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_keys` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(11) unsigned NOT NULL,
  `label` varchar(100) NOT NULL,
  `key` char(40) NOT NULL,
  `ip` varbinary(16) DEFAULT NULL,
  `accessed` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_keys`
--

LOCK TABLES `omeka_keys` WRITE;
/*!40000 ALTER TABLE `omeka_keys` DISABLE KEYS */;
/*!40000 ALTER TABLE `omeka_keys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_options`
--

DROP TABLE IF EXISTS `omeka_options`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_options` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `value` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=83 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_options`
--

LOCK TABLES `omeka_options` WRITE;
/*!40000 ALTER TABLE `omeka_options` DISABLE KEYS */;
INSERT INTO `omeka_options` VALUES (1,'omeka_version','3.2'),(7,'thumbnail_constraint','200'),(8,'square_thumbnail_constraint','200'),(9,'fullsize_constraint','800'),(10,'per_page_admin','10'),(11,'per_page_public','10'),(12,'show_empty_elements','0'),(14,'admin_theme','default'),(16,'file_extension_whitelist','aac,aif,aiff,asf,asx,avi,bmp,c,cc,class,css,divx,doc,docx,exe,gif,gz,gzip,h,ico,j2k,jp2,jpe,jpeg,jpg,m4a,m4v,mdb,mid,midi,mov,mp2,mp3,mp4,mpa,mpe,mpeg,mpg,mpp,odb,odc,odf,odg,odp,ods,odt,ogg,opus,pdf,png,pot,pps,ppt,pptx,qt,ra,ram,rtf,rtx,swf,tar,tif,tiff,txt,wav,wax,webm,wma,wmv,wmx,wri,xla,xls,xlsx,xlt,xlw,zip'),(17,'file_mime_type_whitelist','application/msword,application/ogg,application/pdf,application/rtf,application/vnd.ms-access,application/vnd.ms-excel,application/vnd.ms-powerpoint,application/vnd.ms-project,application/vnd.ms-write,application/vnd.oasis.opendocument.chart,application/vnd.oasis.opendocument.database,application/vnd.oasis.opendocument.formula,application/vnd.oasis.opendocument.graphics,application/vnd.oasis.opendocument.presentation,application/vnd.oasis.opendocument.spreadsheet,application/vnd.oasis.opendocument.text,application/x-ms-wmp,application/x-ogg,application/x-gzip,application/x-msdownload,application/x-shockwave-flash,application/x-tar,application/zip,audio/aac,audio/aiff,audio/mid,audio/midi,audio/mp3,audio/mp4,audio/mpeg,audio/mpeg3,audio/ogg,audio/wav,audio/wma,audio/x-aac,audio/x-aiff,audio/x-m4a,audio/x-midi,audio/x-mp3,audio/x-mp4,audio/x-mpeg,audio/x-mpeg3,audio/x-mpegaudio,audio/x-ms-wax,audio/x-realaudio,audio/x-wav,audio/x-wma,image/bmp,image/gif,image/icon,image/jpeg,image/pjpeg,image/png,image/tiff,image/x-icon,image/x-ms-bmp,text/css,text/plain,text/richtext,text/rtf,video/asf,video/avi,video/divx,video/mp4,video/mpeg,video/msvideo,video/ogg,video/quicktime,video/webm,video/x-m4v,video/x-ms-wmv,video/x-msvideo'),(18,'disable_default_file_validation',''),(20,'display_system_info','1'),(21,'html_purifier_is_enabled','1'),(22,'html_purifier_allowed_html_elements','p,br,strong,em,span,div,ul,ol,li,a,h1,h2,h3,h4,h5,h6,address,pre,table,tr,td,blockquote,thead,tfoot,tbody,th,dl,dt,dd,q,small,strike,sup,sub,b,i,big,small,tt'),(23,'html_purifier_allowed_html_attributes','*.style,*.class,a.href,a.title,a.target'),(26,'search_record_types','a:3:{s:4:\"Item\";s:4:\"Item\";s:4:\"File\";s:4:\"File\";s:10:\"Collection\";s:10:\"Collection\";}'),(29,'show_element_set_headings','1'),(30,'use_square_thumbnail','1'),(33,'omeka_update','a:2:{s:14:\"latest_version\";s:4:\"3.2\n\";s:12:\"last_updated\";i:1779194692;}'),(62,'site_title','Музей \"Архів\"'),(63,'description','Інформаційна система обліку музейних експонатів'),(64,'administrator_email','admin@museum.ua'),(65,'copyright',''),(66,'author',''),(67,'tag_delimiter',','),(68,'path_to_convert',''),(70,'theme_berlin_options','a:13:{s:4:\"logo\";N;s:12:\"header_image\";N;s:16:\"header_image_alt\";N;s:21:\"display_featured_item\";s:1:\"1\";s:27:\"display_featured_collection\";s:1:\"1\";s:24:\"display_featured_exhibit\";s:1:\"1\";s:21:\"homepage_recent_items\";N;s:13:\"homepage_text\";N;s:11:\"footer_text\";N;s:24:\"display_footer_copyright\";s:1:\"0\";s:19:\"use_advanced_search\";s:1:\"0\";s:17:\"item_file_display\";s:1:\"0\";s:17:\"theme_config_csrf\";N;}'),(71,'public_navigation_main','[{\"uid\":\"\\/omeka\\/items\\/browse\",\"can_delete\":false,\"label\":\"Browse Items\",\"fragment\":null,\"id\":null,\"class\":null,\"title\":null,\"target\":null,\"accesskey\":null,\"rel\":[],\"rev\":[],\"customHtmlAttribs\":[],\"order\":1,\"resource\":null,\"privilege\":null,\"active\":false,\"visible\":true,\"type\":\"Omeka_Navigation_Page_Uri\",\"pages\":[],\"uri\":\"\\/omeka\\/items\\/browse\"},{\"uid\":\"\\/omeka\\/collections\\/browse\",\"can_delete\":false,\"label\":\"Browse Collections\",\"fragment\":null,\"id\":null,\"class\":null,\"title\":null,\"target\":null,\"accesskey\":null,\"rel\":[],\"rev\":[],\"customHtmlAttribs\":[],\"order\":2,\"resource\":null,\"privilege\":null,\"active\":false,\"visible\":true,\"type\":\"Omeka_Navigation_Page_Uri\",\"pages\":[],\"uri\":\"\\/omeka\\/collections\\/browse\"},{\"uid\":\"\\/omeka\\/feedback\",\"can_delete\":false,\"label\":\"\\u0417\\u0432\\u043e\\u0440\\u043e\\u0442\\u043d\\u0438\\u0439 \\u0437\\u0432\'\\u044f\\u0437\\u043e\\u043a\",\"fragment\":null,\"id\":null,\"class\":null,\"title\":null,\"target\":null,\"accesskey\":null,\"rel\":[],\"rev\":[],\"customHtmlAttribs\":[],\"order\":3,\"resource\":null,\"privilege\":null,\"active\":false,\"visible\":true,\"type\":\"Omeka_Navigation_Page_Uri\",\"pages\":[],\"uri\":\"\\/omeka\\/feedback\"}]'),(72,'homepage_uri','/'),(74,'theme_seasons_options','a:13:{s:11:\"style_sheet\";s:6:\"winter\";s:4:\"logo\";N;s:21:\"display_featured_item\";s:1:\"1\";s:27:\"display_featured_collection\";s:1:\"1\";s:24:\"display_featured_exhibit\";s:1:\"1\";s:21:\"homepage_recent_items\";N;s:13:\"homepage_text\";N;s:11:\"footer_text\";N;s:24:\"display_footer_copyright\";s:1:\"0\";s:17:\"item_file_gallery\";s:1:\"0\";s:19:\"use_advanced_search\";s:1:\"1\";s:12:\"exhibits_nav\";s:4:\"side\";s:17:\"theme_config_csrf\";N;}'),(76,'api_enable','1'),(77,'api_filter_element_texts',''),(78,'api_per_page','50'),(79,'exhibit_builder_sort_browse','added'),(80,'exhibit_builder_researcher_permissions',''),(81,'public_theme','default'),(82,'theme_default_options','a:20:{s:10:\"text_color\";s:7:\"#393939\";s:16:\"background_color\";s:7:\"#FFFFFF\";s:10:\"link_color\";s:7:\"#555555\";s:12:\"button_color\";s:7:\"#000000\";s:17:\"button_text_color\";s:7:\"#FFFFFF\";s:18:\"header_title_color\";s:7:\"#000000\";s:4:\"logo\";N;s:17:\"header_background\";N;s:11:\"footer_text\";N;s:24:\"display_footer_copyright\";s:1:\"0\";s:21:\"display_featured_item\";s:1:\"1\";s:27:\"display_featured_collection\";s:1:\"1\";s:24:\"display_featured_exhibit\";s:1:\"1\";s:25:\"display_featured_subtitle\";s:1:\"0\";s:21:\"homepage_recent_items\";N;s:13:\"homepage_text\";N;s:17:\"item_file_gallery\";s:1:\"1\";s:19:\"use_advanced_search\";s:1:\"1\";s:27:\"use_original_thumbnail_size\";s:1:\"0\";s:17:\"theme_config_csrf\";N;}');
/*!40000 ALTER TABLE `omeka_options` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_plugins`
--

DROP TABLE IF EXISTS `omeka_plugins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_plugins` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `active` tinyint(4) NOT NULL,
  `version` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `active_idx` (`active`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_plugins`
--

LOCK TABLES `omeka_plugins` WRITE;
/*!40000 ALTER TABLE `omeka_plugins` DISABLE KEYS */;
INSERT INTO `omeka_plugins` VALUES (1,'Feedback',1,'1.0'),(2,'DonateButton',1,'1.0'),(3,'ItemViews',1,'1.0'),(4,'DailyItem',1,'1.0'),(5,'QRCode',1,'1.0'),(6,'ExhibitBuilder',1,'3.8');
/*!40000 ALTER TABLE `omeka_plugins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_processes`
--

DROP TABLE IF EXISTS `omeka_processes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_processes` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `class` varchar(255) NOT NULL,
  `user_id` int(10) unsigned NOT NULL,
  `pid` int(10) unsigned DEFAULT NULL,
  `status` enum('starting','in progress','completed','paused','error','stopped') NOT NULL,
  `args` text NOT NULL,
  `started` timestamp NOT NULL DEFAULT '1999-12-31 22:00:00',
  `stopped` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `pid` (`pid`),
  KEY `started` (`started`),
  KEY `stopped` (`stopped`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_processes`
--

LOCK TABLES `omeka_processes` WRITE;
/*!40000 ALTER TABLE `omeka_processes` DISABLE KEYS */;
/*!40000 ALTER TABLE `omeka_processes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_records_tags`
--

DROP TABLE IF EXISTS `omeka_records_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_records_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `record_id` int(10) unsigned NOT NULL,
  `record_type` varchar(50) NOT NULL DEFAULT '',
  `tag_id` int(10) unsigned NOT NULL,
  `time` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `tag` (`record_type`,`record_id`,`tag_id`),
  KEY `tag_id` (`tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_records_tags`
--

LOCK TABLES `omeka_records_tags` WRITE;
/*!40000 ALTER TABLE `omeka_records_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `omeka_records_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_schema_migrations`
--

DROP TABLE IF EXISTS `omeka_schema_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_schema_migrations` (
  `version` varchar(16) NOT NULL,
  UNIQUE KEY `unique_schema_migrations` (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_schema_migrations`
--

LOCK TABLES `omeka_schema_migrations` WRITE;
/*!40000 ALTER TABLE `omeka_schema_migrations` DISABLE KEYS */;
INSERT INTO `omeka_schema_migrations` VALUES ('20100401000000'),('20100810120000'),('20110113000000'),('20110124000001'),('20110301103900'),('20110328192100'),('20110426181300'),('20110601112200'),('20110627223000'),('20110824110000'),('20120112100000'),('20120220000000'),('20120221000000'),('20120224000000'),('20120224000001'),('20120402000000'),('20120516000000'),('20120612112000'),('20120623095000'),('20120710000000'),('20120723000000'),('20120808000000'),('20120808000001'),('20120813000000'),('20120914000000'),('20121007000000'),('20121015000000'),('20121015000001'),('20121018000001'),('20121110000000'),('20121218000000'),('20130422000000'),('20130426000000'),('20130429000000'),('20130701000000'),('20130809000000'),('20140304131700'),('20150211000000'),('20150310141100'),('20150814155100'),('20151118214800'),('20151209103299'),('20151209103300'),('20161209171900'),('20170331084000'),('20170405125800'),('20200127165700'),('20240709181800'),('20240713184500'),('20240713211400'),('20240717204800'),('20240917160000');
/*!40000 ALTER TABLE `omeka_schema_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_search_texts`
--

DROP TABLE IF EXISTS `omeka_search_texts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_search_texts` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `record_type` varchar(30) NOT NULL,
  `record_id` int(10) unsigned NOT NULL,
  `public` tinyint(1) NOT NULL,
  `title` mediumtext DEFAULT NULL,
  `text` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `record_name` (`record_type`,`record_id`),
  FULLTEXT KEY `text` (`text`)
) ENGINE=MyISAM AUTO_INCREMENT=31 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_search_texts`
--

LOCK TABLES `omeka_search_texts` WRITE;
/*!40000 ALTER TABLE `omeka_search_texts` DISABLE KEYS */;
INSERT INTO `omeka_search_texts` VALUES (1,'Collection',1,1,'Археологія','Археологія Археологічні знахідки з розкопок на території України '),(3,'Item',1,1,' Скляні браслети ',' Скляні браслети  Під час розкопок віднайдено фрагменти амфор, які виготовлялися у Візантії, уламки скляних браслетів немісцевого походження ХІІ–ХІІІ ст. місто Белз (Сокальський район Львівщини)  '),(7,'Collection',6,1,'Зброя','Зброя Предмети озброєння та військового спорядження різних епох: холодна та вогнепальна зброя, захисне спорядження козацького та середньовічного періодів '),(8,'Collection',7,1,'Побут та ремесла','Побут та ремесла Предмети повсякденного побуту та народного мистецтва Львівщини XIX–XX століть: вишивка, кераміка, дерев\'яні вироби, металеві предмети домашнього вжитку '),(6,'Collection',5,1,'Документи та карти\r\n','Документи та карти\r\n Історичні документи, грамоти, картографічні матеріали та рукописи, що відображають адміністративну та культурну історію Львова і Львівського регіону XVII–XX століть '),(9,'Collection',8,1,'Фотографії','Фотографії Фотографічні матеріали кінця XIX – першої половини XX століття, що документують вигляд міста Львова, його вулиць, площ та архітектурних пам\'яток '),(10,'Item',2,1,'Старовинний український керамічний глечик, виріб Опішнянської кераміки','Старовинний український керамічний глечик, виріб Опішнянської кераміки Старовинний український керамічний глечик, який є виробом Опішнянської кераміки. Виготовлений вручну, характерний для традиційного гончарства Полтавщини. Прикрашений поливою та мальованим рослинним орнаментом. Глечик використовують для зберігання рідин, головним чином, молочних продуктів (молока, сметани тощо). Незамінний атрибут українського сільського побуту.  XIX ст. Фізичний об\'єкт Полтавщина '),(11,'Item',3,1,'Кам\'яний наконечник стріли','Кам\'яний наконечник стріли Крем\'яна стріла. Наконечник до стріли - крем\'яний, червонуватого кольору, трикутноподібної форми, при основі вигнутий до середини. По обох боках лезо ретушоване. Кремнієві та кам\'яні наконечники - інструменти періоду неоліту. Використовувалися людиною у повсякденному житт Період неоліту Фізичний об\'єкт Кременець '),(12,'Item',4,1,'Козацькі шаблі. XVII – XVIII ст.','Козацькі шаблі. XVII – XVIII ст. Шабля є різновидом холодної зброї з довгим викривленим клинком, призначена для нанесення рубаючо-ріжучих та колючих ударів. Козаки здебільшого використовували трофейну і покупну зброю, яка походила із різних кутків світу. На території України масово шаблі не виготовлялися, за винятком Львова, який мав розвинені ковальські цехи, але на той момент був під владою Польщі. Серед шабель, які експонуються в Історичному музеї, є шаблі польського, італійського, турецького та козацького виробництва. Вони відрізняються формою та оздобленістю клинка та рукояті. Наприклад, на козацькій шаблі зображено перехрещені булава та пірнач і напис: «За верность земле и преданиям». Шабля один із головних козачих атрибутів, це не просто кривий меч – це символ лицаря і вільної людини. Крім того козаки мали по декілька шабель – «чорну» і «білу», одна була бойовою, а інша парадна, яка носилась на свята. XVII – XVIII ст. Фізичний об\'єкт Дніпропетровська область '),(13,'Item',5,1,'Мушкет','Мушкет Кремінний мушкет виробництва Османської імперії XVIII століття. Зброя потрапила на територію Галичини під час військових конфліктів між Річчю Посполитою та Османською імперією. Відзначається характерним декором ложа з перламутровими інкрустаціями, типовими для османського зброярського мистецтва. XVIII ст. Османська імперія, '),(14,'Item',6,1,'Мушкет','Мушкет Кремінний мушкет виробництва Османської імперії XVIII століття. Зброя потрапила на територію Галичини під час військових конфліктів між Річчю Посполитою та Османською імперією. Відзначається характерним декором ложа з перламутровими інкрустаціями, типовими для османського зброярського мистецтва. XVIII ст. Османська імперія, '),(16,'Item',7,1,'Жіноча вишиванка ','Жіноча вишиванка  \r\nСорочка жіноча вишивка,кінець 19 століття,початок 20 століття ХІХ ст. Хмельницька область '),(17,'Item',8,1,'Скриня різьблена','Скриня різьблена тип орнаменту:  геометричний\r\nТехніки:  ковальська техніка / столярна техніка / різьблення плоске / тонування / розпис / вирізування кінець ХІХ ст. Фізичний об\'єкт Гуцульщина '),(18,'Item',9,1,'Бойова сокира','Бойова сокира Форма цього екземпляру, вочевидь, місцева, аналогії їй відомі та датуються доволі широким часовим періодом Х-ХІІІ століть. Проте мотив орнаменту рідкісний, якщо не сказати – унікальний. За окремими елементами, з яких складається орнамент, його можна датувати в межах вужчого часу, від кінця Х до початку ХІ століть. Цьому відповідає й інкрустація тризубом, іконографія якого датується періодом княжіння Володимира Святославича Х-ХІІІ ст. Фізичний об\'єкт Львівщина '),(19,'Item',10,1,'Свічник-трійця','Свічник-трійця Трійці – це різьблені, часто пишно декоровані трисвічники, які мають церковно-літургійне та обрядово-побутове застосування. Термін «гуцульські та покутські свічники-трійці» давно увійшов у науковий обіг. Цей вислів акцентує, що названий вид дерев’яної пластики характерний лише для Гуцульщини та Покуття. Утім навіть на такій невеликій території трійці побутують вкрай нерівномірно. Аналіз зібраного матеріалу дає можливість простежити походження трисвічників із 37 гуцульських та 42 покутських сіл. що свідчить про винятково локальний характер цього виду народного мистецтва. Друга пол. ХІХ ст. Фізичний об\'єкт с. Нижній Березів Косівського р-ну Івано-Франківської обл. '),(20,'Item',11,1,'Австрійська карта Львова 1844 року','Австрійська карта Львова 1844 року План території Львова є оригіналом фотозйомки виконаної Віденським військово-географічним інститутом. План датований 1844 роком. На аркуші плану розміщено прізвища його авторів: Кратохвіль (Kratochwill), Радайчіч (Radaichich), Кранковіч (Krankowich). \r\nЛегенда:\r\n\r\nУ правому верхньому куті розташовано назву: \"Лемберг з його передмістями у 1844 році\" (Lemberg mit seinen Vorstadten im Jahre 1844).\r\nНижче розміщено мірну лінію із написом: \"1 віденському дюйму відповідає 100 сажнів або 250 кроків на місцевості\" (1 Wiener Zoll = 100 Klafter oder 250 Schritte). Масштаб плану в числовому еквіваленті - 1:7 200 [12], c. 228.\r\nПісля мірної лінії розташовано перелік умовних позначень та інформацію про поділ міста на передмістя:\r\n\"Перша дільниця або Галицьке передмістя\" (1-tes Viertel oder Halitcher Vorstadt).\r\n\"Друга дільниця або Краківське передмістя\" (2-tes Viertel oder Krakauer Vorstadt).\r\n\"Третя дільниця або Жовківське передмістя\" (3-tes Viertel oder Żolkiewer Vorstadt).\r\n\"Четверта дільниця або Бродівське передмістя\" (4-tes Viertel oder Brodyer Vorstadt).\r\n\"Місто\" (Stadt).\r\nУ правому нижньому куті міститься перелік із 26 важливих будівель в Середмісті (Bezeichnung der vorzüglichsten Gebaede in der Stadt).\r\nНижче розміщено напис (auf Stein gest. und [] Kratochwill und Rado[iс]sich geschrieben Krankowich).\r\nУ правому лівому куті розташовано перелік із 91-ї важливої будівлі на територіях чотирьох дільниць міста (Bezeichnung der vorzüglichsten Gebaede in der Stadt). 1844 Картографічний матеріал Львів '),(21,'Item',12,1,'Грамота базельського синоду','Грамота базельського синоду Документ оздоблений декоративним заголовком та вислою металевою печаткою, яка підтверджує його автентичність.\r\nрамота написана в період роботи Базельського собору католицької церкви (1431–1449), скликаного папою Мартином V для реформування церкви та врегулювання військового конфлікту з гуситами. Відповідно до неї львівському архієпископу Одровонжу Івану передавалася частина судових і адміністративних повноважень. Ця грамота фактично посилювала автономію Львівської архідієцезії, дозволяючи вирішувати частину таких справ на місці, без апеляції до Риму. Це прискорювало судочинство і зміцнювало роль архієпископа в регіоні. 1431–1449 Текстовий документ Зберігається у Центральному державному сторичному архіві України, м. Львів, (фонд № 131 «Колекція грамот на пергаменті» , оп. 1, спр. 119). '),(22,'Item',13,1,'Вид центру Львова 1924 року','Вид центру Львова 1924 року У 1924 році Львів, місто з багатовіковою історією, переживало період значних змін та трансформацій. Після буремних років Першої світової війни та польсько-української війни 1918-1919 років місто опинилося у складі Другої Польської Республіки. Згідно з Ризьким мирним договором 1921 року, Львів став адміністративним центром Львівського воєводства.\r\nНа початку 1924 року посаду воєводи Львівського воєводства обіймав Kazimierz Grabowski (Казімєж Грабовський), який був звільнений з цієї посади 30 червня 1924 року. Після нього короткий період обов’язки виконував Stanisław Zimny (Станіслав Зимний), а потім на цю посаду був призначений Paweł Garapich (Павел Гарапіх), який залишався воєводою до 1927 року​. Міським головою Львова в цей час був Józef Neumann (Йозеф Нойманн) який обіймав цю посаду з 1918 до 1927 року. 1924р Зображення Львів '),(23,'Item',14,1,'Карта Боплана','Карта Боплана Культурно-просвітницький центр Alex Art House – це три галереї приватних колекцій та Музей стародавньої книги. Основу експозиції галерей складають… карти. Зокрема карти французького картографа та інженера Ґійома Левассера де Боплана. Серед раритетів – астрономічні карти німецького астронома і математика 17 століття  Йоганна Доппельмайра. Особливу історичну цінність мають дві карти зображення України 1478 року з Римського видання географічної праці Клавдія Птолемея «Космографія». Ці карти належать до ранніх зразків гравюри на міді і є одними з перших в історії друкованих карт.\r\n\r\n 1478\r\n Картографічний матеріал Київщина '),(24,'Item',15,1,'Личаківський цвинтар початку XX століття','Личаківський цвинтар початку XX століття Історія цвинтаря починається з 1786 року після заборони здійснювати поховання навколо храмів у межах міста. Личаківський цвинтар один з чотирьох, які тоді функціонували у Львові, і єдиний, який зберігся до сьогодні. Але знайти поховання, які з’являлися тут у ті роки, майже неможливо, бо в середині ХІХ ст. почало діяти нововведення магістрату, яке передбачало встановлення каменедробарки на кладовищі. Так, надгробки над могилами, які не доглядали родичі упродовж 25 років, перемелювали на дрібне каміння, яким вистеляли доріжки, а пізніше збудували цвинтарну браму. 1900 Зображення Львів '),(25,'Item',16,1,'Діорама «Поховання знатного скіфа»','Діорама «Поховання знатного скіфа» Діорама відтворює обряд поховання знатного представника скіфської культури. Скіфи — кочовий іраномовний народ, що населяв територію Північного Причорномор\'я у VII–III століттях до нашої ери. Поховальний обряд знатних скіфів відрізнявся особливою пишністю: разом із небіжчиком у курган клали зброю, коштовності, посуд та жертвували коней. Діорама є реконструкцією на основі археологічних матеріалів скіфських курганів. VII–III ст. до н.е. Діорама Північне Причорномор\'я '),(26,'Item',17,1,'Діорама «Київ. Місто Володимира»','Діорама «Київ. Місто Володимира» Діорама відтворює вигляд давньоруського Києва часів князя Володимира Великого (980–1015 рр.). Місто Володимира — укріплена частина Києва, збудована за часів правління князя Володимира Святославича. Включала Десятинну церкву, князівський палац та систему укріплень. Саме тут у 988 році відбулося хрещення Русі. Діорама створена на основі археологічних досліджень та історичних джерел. X–XI ст. Діорама Київ, Київська Русь '),(27,'Item',18,1,'Копія Золотої пекторалі','Копія Золотої пекторалі Копія знаменитої золотої пекторалі — нагрудної прикраси скіфського царя, знайденої у кургані Товста Могила на Дніпропетровщині у 1971 році археологом Борисом Мозолевським. Оригінал датується IV століттям до нашої ери та зберігається у Національному музеї історії України у Києві. Пектораль важить 1148 грамів та має діаметр 30,6 см. Складається з трьох ярусів: нижній зображує сцени боротьби тварин, середній — рослинний орнамент, верхній — сцени мирного скіфського побуту. Вважається шедевром ювелірного мистецтва античного світу. IV ст. до н.е. (копія — XX ст.) Ювелірний виріб (копія) Дніпропетровська область, курган Товста Могила '),(28,'Item',19,1,'Фунікулер','Фунікулер Київський фунікулер — канатний підйомник, збудований у 1905 році для зв\'язку Верхнього міста з Подолом. Споруджений на залізобетонній естакаді з прокладеними рейками. Став вирішенням транспортної проблеми крутих схилів між двома частинами міста. Один з найстаріших фунікулерів на території України, що функціонує донині. 1905 Зображення Київ '),(29,'Exhibit',1,1,'Київ у минулому столітті','Київ у минулому столітті  '),(30,'ExhibitPage',1,1,'Київ','   Київ ');
/*!40000 ALTER TABLE `omeka_search_texts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_sessions`
--

DROP TABLE IF EXISTS `omeka_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_sessions` (
  `id` varchar(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `modified` bigint(20) DEFAULT NULL,
  `lifetime` int(11) DEFAULT NULL,
  `data` blob DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `modified` (`modified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_sessions`
--

LOCK TABLES `omeka_sessions` WRITE;
/*!40000 ALTER TABLE `omeka_sessions` DISABLE KEYS */;
INSERT INTO `omeka_sessions` VALUES ('0212m6r0mqt6ddeeppobhpc38g',1778367037,1209600,''),('0338ndtns5f5s081s526o8m0h8',1778370051,1209600,''),('1c3dhau0edqe1bf410bvdep9qq',1778374268,1209600,''),('1r4op5h7r8q4fje3378ns890n6',1778370208,1209600,''),('20jpt5gh111ldc0vmdg8rc3q1k',1778376462,1209600,''),('211cgj6f8tnhcj3uud2sghssqh',1778367584,1209600,''),('23nut5vnbo4rncjmc52kikliph',1778370052,1209600,''),('2jtkp5bhb281o2d750h4uu856k',1778376445,1209600,''),('2ql5bavsggrdeurtb6ue4hf0cr',1778369689,1209600,''),('2s73t0q48h32486m00v4jkuj4u',1778391412,1209600,''),('35h3cpt686uvpkkavg8rror9op',1778370014,1209600,''),('3hnsdhulmdaccl5pfcf3c9quci',1778370210,1209600,''),('3jo5s32vlncfd7j4ubokpft6rg',1778368499,1209600,''),('3nhdjo8gf5d870ph0pjcdp9sad',1778370209,1209600,''),('3u9hkvnogsv153k6s69e66mkl6',1778361510,1209600,''),('53o937rbh63ndi5mtnoekbnlnj',1778367196,1209600,''),('58lipvi1m9o4i0d15as3jmnm70',1778370037,1209600,''),('59rchs8k5tnu0a08g4uae63s7q',1778368501,1209600,''),('5hk57f71c3u28mtqu80s88vrj3',1778374127,1209600,''),('5q2969lm030j7v1i2l9lrce0r8',1778367033,1209600,''),('67mlvnof1pljj1qb4pdi0ushpr',1778369076,1209600,''),('6fpq83uc52dea966vvo305u1em',1778373904,1209600,''),('6h9v24t368jmn487s4knohtcjj',1778370026,1209600,''),('6k229fhuil8gjen6lebke11cvp',1778370322,1209600,''),('6m48cvhg61d0rpf5va83d0mv6t',1778367584,1209600,''),('6oelkko4h8drcf2cjjl38um42q',1778365185,1209600,''),('816gqavue4uak2ipl4k01b18io',1778373629,1209600,''),('8mltq2drhvrjatiufglpg4spse',1778370053,1209600,''),('8p23u77v43th487qgrm548rgsp',1778374145,1209600,''),('98l31vhjranbda612ua3fkbkaq',1778370052,1209600,''),('9einuabemcgd952tjs6jouunon',1778367195,1209600,''),('9m9pkhrp0r01i2345dc8nc5ini',1778370320,1209600,''),('as1365fpq5pg3168tpvl15okqc',1778369076,1209600,''),('auosgtfjf18e3d9ve59o27h2g1',1778370209,1209600,''),('b396lp9rhrccdh5gj664h065gd',1778370036,1209600,''),('bd01grtdsv25958mbdgoheiui6',1778370036,1209600,''),('bsntbbg48smonkn88i1uhnbj8e',1778375602,1209600,''),('crv7hloc04jhqepbf941rdi32h',1778370025,1209600,''),('d30jdrlm50nudncrb27b3udvlr',1778367583,1209600,''),('do8uchi9agrlova4e8uake1ch0',1778370024,1209600,''),('e099ihatjouec2r8skhkp1m5i0',1778367199,1209600,''),('e3rptghu9dmhfgboo78q0fai8h',1778375795,1209600,''),('ep107r5r60lh534d1s3qctmg0g',1778375795,1209600,''),('f1afj8gkgibpct2q65pp62amoi',1778369075,1209600,''),('f2eg7lucok77mlmknn5btar5oj',1778367769,1209600,'Default|a:1:{s:8:\"redirect\";s:1:\"/\";}Zend_Auth|a:1:{s:7:\"storage\";i:1;}__ZF|a:2:{s:41:\"Zend_Form_Element_Hash_salt_settings_csrf\";a:2:{s:4:\"ENNH\";i:1;s:3:\"ENT\";i:1778371364;}s:14:\"FlashMessenger\";a:1:{s:4:\"ENNH\";i:1;}}Zend_Form_Element_Hash_salt_settings_csrf|a:1:{s:4:\"hash\";s:32:\"2c33c05b5bd2ba7ad123449035bb191f\";}OmekaSessionCsrfToken|a:1:{s:5:\"token\";s:32:\"93b931057a239fcbd1c43f82e8739d60\";}'),('f4eacelbrjvn1hu3m75lds5epj',1778374127,1209600,''),('f7fjj59nvmtqekcjsubv9jccn8',1778374145,1209600,''),('ffp3445fmc7q9a5m0c3qev3fue',1778373341,1209600,''),('fi51d22f8qaschd5o0c6k61pk8',1778373629,1209600,''),('gasfn8d3cu8id4b2eu5l0dec1u',1778374268,1209600,''),('h2ggqr6k731trojl9q3kv00vuc',1778370037,1209600,''),('hrnhhrqp4p69h8bjv8iumhrt3h',1778373309,1209600,''),('k8etebeakpn021uftsub1e5mgs',1778376463,1209600,''),('kiterrdiec8a96juoe912bq0n9',1778374775,1209600,''),('kjvo75vn41i0b11mld37roa5kl',1778369074,1209600,''),('l585acekerb07bbsjts9ud3cn7',1778370013,1209600,''),('l8cd63igq2737g0o3jra9dpfa0',1778370320,1209600,''),('lfgrefqiglqsvu7m52u52smp64',1778369690,1209600,''),('lhtr3nqotp865t6qc0u8s9h9cb',1778391411,1209600,''),('ls7cic0ploet6i6ppl5b3ghfrh',1778367585,1209600,''),('lscjprjqts4hj5cvjr10q93hu3',1778373904,1209600,''),('mj63pfeauij29vop1madr6v53o',1778373341,1209600,''),('n4rrcuh0erorjbbpmcpti17fqb',1778361708,1209600,''),('o03he1pvvqutpu4h7nbisdbn6g',1778370025,1209600,''),('ov69t6md5gdhfcl57dq0pn617o',1778371214,1209600,''),('p4vlrg3mtg9rt9t41afp5uupuc',1778371214,1209600,''),('p5t8q7elnapjvs5s74gvs1u61i',1778374775,1209600,''),('pml17mdi9m8bv41q0vetrl11ak',1778370013,1209600,''),('qnkkj4uol97n3gbfpu1fqhof0l',1778375603,1209600,''),('qnttn30h64njjvpsb89j33bc46',1778370321,1209600,''),('qr1jlf4d3r56d5co0qk3396jhr',1778368502,1209600,''),('rnvaie070qln7o23p5b9s28i7v',1778367035,1209600,''),('rptq5ckl70tdvg88b8aq4euk6a',1778368500,1209600,''),('sgv3rujqkq747r6jlgp84i147j',1778369688,1209600,''),('t4uofuv96d4clj1mnftfa8i263',1778391412,1209600,''),('t8kuo7b815qs2metcjdh083s6a',1778373310,1209600,''),('tl0onqsoioh9b6fma70l26smn3',1778367038,1209600,''),('u6cgsuet98v2rm0dit77ji7eha',1778376445,1209600,''),('ui5oahlffq04bstlaibkvdldtc',1778369689,1209600,''),('ume0f6aujia48ljh2rqajh72co',1778367038,1209600,''),('utoj43vj836hqlmn61g3fpctlu',1778391413,1209600,''),('v9f57bgumd6e82uhgsq9938q6q',1778367034,1209600,''),('vj40blqjch1aaor1vpqdlnggjj',1778367032,1209600,''),('vk45g22t898b9bdc9ukfo98cku',1778370012,1209600,''),('vo1uuvqkalj0b7tpka7qqeo53p',1778367198,1209600,''),('vpsg7ikc8j788fmh3dlrmqbckv',1779350340,1209600,'Default|a:1:{s:8:\"redirect\";s:1:\"/\";}Zend_Auth|a:1:{s:7:\"storage\";i:1;}OmekaSessionCsrfToken|a:1:{s:5:\"token\";s:32:\"b3e1914b38adf204f4c047a7e5fb909d\";}__ZF|a:1:{s:43:\"Zend_Form_Element_Hash_salt_navigation_csrf\";a:2:{s:4:\"ENNH\";i:1;s:3:\"ENT\";i:1779352257;}}Zend_Form_Element_Hash_salt_navigation_csrf|a:1:{s:4:\"hash\";s:32:\"9d0d3b498c87455ed217835bf689fce3\";}');
/*!40000 ALTER TABLE `omeka_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_tags`
--

DROP TABLE IF EXISTS `omeka_tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_tags` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_tags`
--

LOCK TABLES `omeka_tags` WRITE;
/*!40000 ALTER TABLE `omeka_tags` DISABLE KEYS */;
/*!40000 ALTER TABLE `omeka_tags` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_users`
--

DROP TABLE IF EXISTS `omeka_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_users` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(30) NOT NULL,
  `name` text NOT NULL,
  `email` text NOT NULL,
  `password` varchar(255) CHARACTER SET ascii COLLATE ascii_bin DEFAULT NULL,
  `salt` varchar(16) DEFAULT NULL,
  `active` tinyint(4) NOT NULL,
  `role` varchar(40) NOT NULL DEFAULT 'default',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `active_idx` (`active`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_users`
--

LOCK TABLES `omeka_users` WRITE;
/*!40000 ALTER TABLE `omeka_users` DISABLE KEYS */;
INSERT INTO `omeka_users` VALUES (1,'admin','Super User','admin@museum.ua','$2y$10$ZrfcNuVxXuAlRB7UulV50.qYsHS1g2IAx1tupHRRCz15wQAgqoNU2','bcrypt',1,'super');
/*!40000 ALTER TABLE `omeka_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `omeka_users_activations`
--

DROP TABLE IF EXISTS `omeka_users_activations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `omeka_users_activations` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `url` varchar(100) DEFAULT NULL,
  `added` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `omeka_users_activations`
--

LOCK TABLES `omeka_users_activations` WRITE;
/*!40000 ALTER TABLE `omeka_users_activations` DISABLE KEYS */;
/*!40000 ALTER TABLE `omeka_users_activations` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-21 11:04:56
