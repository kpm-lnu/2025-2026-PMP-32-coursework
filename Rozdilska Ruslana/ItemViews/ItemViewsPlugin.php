<?php
class ItemViewsPlugin extends Omeka_Plugin_AbstractPlugin
{
    protected $_hooks = array('install', 'uninstall', 'public_items_show');

    public function hookInstall()
    {
        $db = $this->_db;
        $sql = "CREATE TABLE IF NOT EXISTS `{$db->prefix}item_views` (
            `item_id` INT UNSIGNED NOT NULL,
            `views` INT UNSIGNED NOT NULL DEFAULT 0,
            PRIMARY KEY (`item_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;";
        $db->query($sql);
    }

    public function hookUninstall()
    {
        $db = $this->_db;
        $db->query("DROP TABLE IF EXISTS `{$db->prefix}item_views`");
    }

    public function hookPublicItemsShow($args)
    {
        $item = $args['item']; // Отримуємо поточний експонат
        $db = $this->_db;
        
        $sql = "INSERT INTO `{$db->prefix}item_views` (item_id, views) VALUES ({$item->id}, 1) ON DUPLICATE KEY UPDATE views = views + 1";
        $db->query($sql);
        
        $views = $db->fetchOne("SELECT views FROM `{$db->prefix}item_views` WHERE item_id = ?", array($item->id));
        
        echo "<div style='margin-top: 15px; color: #666;'>&#128065; Цей експонат переглянули: <strong>{$views}</strong> раз(ів)</div>";
    }
}