import logging

def setup_logger():
    logger = logging.getLogger('taskmaster')
    logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler('taskmaster.log')
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    return logger