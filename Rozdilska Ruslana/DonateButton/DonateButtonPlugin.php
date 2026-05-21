<?php
class DonateButtonPlugin extends Omeka_Plugin_AbstractPlugin
{
    protected $_hooks = array('public_items_show');

    public function hookPublicItemsShow($args)
    {
        
        echo '<div style="background: #f4f6f7; padding: 20px; border-left: 5px solid #28a745; margin-top: 30px; border-radius: 4px;">';
        echo '<h3 style="margin-top: 0;">Підтримайте наш музей!</h3>';
        echo '<p>Ваші благодійні внески допомагають нам зберігати історію та цифровізувати нові експонати. <br><b>Реквізити (IBAN):</b> UA123456789000000000000000000</p>';
       echo '<a href="https://send.monobank.ua/jar/1234567890" target="_blank" style="text-decoration: none; display: inline-block; background: #28a745; color: white; padding: 10px 20px; font-size: 16px; border-radius: 3px;">Зробити внесок</a>';
        echo '</div>';
    }
}