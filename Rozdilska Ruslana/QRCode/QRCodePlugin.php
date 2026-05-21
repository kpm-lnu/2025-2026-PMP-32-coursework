<?php
class QRCodePlugin extends Omeka_Plugin_AbstractPlugin
{
    protected $_hooks = array('public_items_show');

    public function hookPublicItemsShow($args)
    {
        $item = $args['item'];
        $url = 'http://' . $_SERVER['HTTP_HOST'] . record_url($item);
        
        $qr_api = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=" . urlencode($url);
        
        echo '<div style="margin-top: 25px; padding: 15px; background: #f9f9f9; border-radius: 5px; display: inline-block; border: 1px solid #ddd;">';
        echo '<p style="margin-top: 0; font-weight: bold; color: #333;">📱 Відскануйте на телефон:</p>';
        echo '<img src="' . $qr_api . '" alt="QR код експоната" style="border: 5px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"/>';
        echo '</div>';
    }
}