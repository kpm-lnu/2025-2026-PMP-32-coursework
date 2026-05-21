<?php
class DailyItemPlugin extends Omeka_Plugin_AbstractPlugin
{
    
    protected $_hooks = array('public_home');

    public function hookPublicHome($args)
    {
        
        $items = get_records('Item', array('sort_field' => 'random'), 1);
        
        if ($items) {
            $item = $items[0];
            $title = metadata($item, array('Dublin Core', 'Title'));
            
            echo '<div style="border: 2px dashed #0056b3; padding: 20px; text-align: center; margin-bottom: 30px; background-color: #f8fbff;">';
            echo '<h2 style="color: #0056b3; margin-top:0;">🌟 Зверніть увагу: Експонат дня!</h2>';
            echo '<h3>' . $title . '</h3>';
            
           
            if (metadata($item, 'has files')) {
                echo files_for_item(array('imageSize' => 'square_thumbnail'), array(), $item);
            }
            
            echo '<p><a href="' . record_url($item) . '" style="display:inline-block; margin-top:15px; padding: 10px 20px; background: #0056b3; color: #fff; text-decoration: none;">Дізнатися більше</a></p>';
            echo '</div>';
        }
    }
}