class MessageFormatter:
    AUTHOR_TEMPLATE = "<b>Author:</b> <i>{}</i>\n\n"
    TITLE_TEMPLATE = "<b>Title:</b> <i>{}</i>\n\n"
    DESCRIPTION_TEMPLATE = "<b>Description:</b> <i>{}</i>\n\n"
    LINK_TEMPLATE = "<b>Link:</b> <i>{}</i>"

    @staticmethod
    def format_message(author, title, description, link):
        formatted_author = MessageFormatter.AUTHOR_TEMPLATE.format(author)
        formatted_title = MessageFormatter.TITLE_TEMPLATE.format(title)
        formatted_description = MessageFormatter.DESCRIPTION_TEMPLATE.format(description)
        formatted_link = MessageFormatter.LINK_TEMPLATE.format(link)
        
        return formatted_author + formatted_title + formatted_description + formatted_link
