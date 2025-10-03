.custom-banner {
        background: linear-gradient(135deg, #5DD9C1 0%, #00A982 100%);
        padding: 20px;
        border-radius: 0 0 15px 15px;
        margin: 0 -70px 30px -70px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }

    .custom-banner::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 50%;
        background: linear-gradient(
            to bottom,
            rgba(255, 255, 255, 0.4) 0%,
            rgba(255, 255, 255, 0.1) 50%,
            transparent 100%
        );
        pointer-events: none;
    }
