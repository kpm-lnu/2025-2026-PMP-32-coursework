<?php
class Feedback_IndexController extends Omeka_Controller_AbstractActionController
{
    public function indexAction()
    {
        if ($this->getRequest()->isPost()) {
            $feedback = new Feedback();
            $feedback->name = $this->getParam('name');
            $feedback->email = $this->getParam('email');
            $feedback->message = $this->getParam('message');
            $feedback->save();
            
            
            try {
                $mail = new Zend_Mail('UTF-8');
                
                $bodyText = "Ви отримали новий відгук на сайті музею:\n\n";
                $bodyText .= "Ім'я: " . $feedback->name . "\n";
                $bodyText .= "Email: " . $feedback->email . "\n";
                $bodyText .= "Повідомлення:\n" . $feedback->message;
                
                $mail->setBodyText($bodyText);
                $mail->setFrom($feedback->email, $feedback->name); 
                
               
                $mail->addTo('below44zero@gmail.com', 'Адміністратор музею'); 
                
                $mail->setSubject('Новий відгук на сайті музею');
                $mail->send();
            } catch (Exception $e) {
                
            }
          
            
            $this->_helper->flashMessenger('Дякуємо за ваш відгук! Ми його отримали.', 'success');
            $this->redirect('feedback');
        }
    }
}