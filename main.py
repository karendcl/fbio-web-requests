import streamlit as st
from model import WebPostRequest

def main():
    st.title("Petición sobre publicación en página web")

    with st.form(key='post_request_form', clear_on_submit=True, enter_to_submit=False):
        user_name = st.text_input("Nombre")
        user_email = st.text_input("Email")
        department = st.selectbox("Departamento",
                                  ["Microbiología",
                                   "Bioquímica",
                                   "Biología Animal y Humana",
                                   "Biología Vegetal",
                                   "CEP",
                                   "Otro"],
                                  help="Seleccione el departamento al que pertenece")
        topic = st.text_input("Tema")
        message = st.text_area("Message")
        images = st.file_uploader("Upload Images", type=['jpg', 'png'], accept_multiple_files=True)

        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            try:
                image_paths = []
                for image in images:
                    image_path = f"data/{image.name}"
                    with open(image_path, "wb") as f:
                        f.write(image.getbuffer())
                    image_paths.append(image_path)
                WebPostRequest(user_name, user_email, topic, message, image_paths, department)
                st.success("Su peticion ha sido enviada con exito. Se le notificará por correo electrónico cuando su publicación sea aprobada. Gracias por su paciencia. ")
                st.balloons()
            except Exception as e:
                st.error(f"Ocurrio un error: {e}."
                         f"Intentelo de nuevo, o si no lo puede solucionar pongase en contacto con el administrador del sistema.")


if __name__ == "__main__":
    main()

