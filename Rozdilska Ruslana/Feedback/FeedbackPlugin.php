<?php
class FeedbackPlugin extends Omeka_Plugin_AbstractPlugin
{
    protected $_hooks = array('install', 'uninstall');
    protected $_filters = array('public_navigation_main');

    public function hookInstall()
    {
        $db = $this->_db;
        $sql = "CREATE TABLE IF NOT EXISTS `{$db->prefix}feedbacks` (
            `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
            `name` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
            `email` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
            `message` TEXT COLLATE utf8_unicode_ci NOT NULL,
            `inserted` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;";
        $db->query($sql);
    }

    public function hookUninstall()
    {
        $db = $this->_db;
        $sql = "DROP TABLE IF EXISTS `{$db->prefix}feedbacks`";
        $db->query($sql);
    }

    public function filterPublicNavigationMain($nav)
    {
        $nav[] = array(
            'label' => __('Зворотний зв\'язок'),
            'uri' => url('feedback')
        );
        return $nav;
    }
}