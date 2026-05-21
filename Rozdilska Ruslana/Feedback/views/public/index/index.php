<?php echo head(array('title' => 'Зворотний зв\'язок з музеєм')); ?>

<h1>Зворотний зв'язок</h1>

<?php echo flash(); ?>

<form method="post" action="<?php echo url('feedback/index/index'); ?>">
    <div class="field">
        <label for="name">Ваше ім'я:</label>
        <div class="inputs">
            <input type="text" name="name" id="name" required>
        </div>
    </div>
    <div class="field">
        <label for="email">Email:</label>
        <div class="inputs">
            <input type="email" name="email" id="email" required>
        </div>
    </div>
    <div class="field">
        <label for="message">Повідомлення / Відгук:</label>
        <div class="inputs">
            <textarea name="message" id="message" rows="6" required></textarea>
        </div>
    </div>
    <div class="submit-button">
        <button type="submit">Відправити відгук</button>
    </div>
</form>

<?php echo foot(); ?>