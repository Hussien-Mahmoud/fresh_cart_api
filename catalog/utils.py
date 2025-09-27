def brand_file_name(instance, filename):
    return f'brands/{instance.name}.{filename.split(".")[-1]}'

def product_cover_file_name(instance, filename):
    return f'products/{instance.name}_cover.{filename.split(".")[-1]}'

def product_images_file_name(instance, filename):
    images_count = instance.product.images.count()
    return f'products/{instance.name}-{images_count + 1}.{filename.split(".")[-1]}'